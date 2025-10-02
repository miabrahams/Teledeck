# Teledeck AI Service Deployment Guide

This guide covers local testing, container builds, and production deployment to Google Cloud for the Teledeck AI inference service. The service exposes both HTTP (FastAPI) and gRPC (image scoring/tagging) interfaces and supports GPU acceleration.

## 1. Prerequisites
- Google Cloud project with billing enabled.
- gcloud CLI ≥ 475.0.0 and Docker installed.
- Artifact Registry API, Cloud Run API, and (optionally) GKE API enabled.
- Access to the model assets under `AI/models/` (tagger checkpoint, tag vocab, aesthetic model folder or checkpoint).

## 2. Local Testing
```bash
# Install Python deps (requires CUDA capable machine for GPU inference)
python -m venv .venv && source .venv/bin/activate
pip install -r AI/requirements.txt

# Start both HTTP (8080) and gRPC (9090) servers
python AI/server.py

# Sample health check
curl http://localhost:8080/health
```

To run gRPC only on port 8080 (useful when emulating Cloud Run):
```bash
ENABLE_HTTP=0 GRPC_PORT=8080 python AI/server.py
```

## 3. Container Build & Test
```bash
# Build locally (context = AI directory)
docker build -f AI/Dockerfile -t teledeck-ai:latest AI

# Run with GPU passthrough
docker run --rm --gpus all -p 8080:8080 -p 9090:9090 \
  -e DEVICE=cuda teledeck-ai:latest
```

## 4. Push Image to Artifact Registry
```bash
REGION=us-central1
PROJECT_ID=your-project
REPO=teledeck
IMAGE=ai-service
TAG=v1

# Create repository once
gcloud artifacts repositories create $REPO \
  --repository-format=docker --location=$REGION

# Configure Docker auth
gcloud auth configure-docker $REGION-docker.pkg.dev

# Build & push
docker build -f AI/Dockerfile -t $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/$IMAGE:$TAG AI
docker push $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/$IMAGE:$TAG
```

## 5. Deploy to Cloud Run (gRPC-only, GPU)
Cloud Run exposes a single port. Deploy the gRPC endpoint (port 8080) and keep REST traffic inside your VPC.
```bash
SERVICE=teledeck-ai-grpc
REGION=us-central1
IMAGE=$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/$IMAGE:$TAG

gcloud run deploy $SERVICE \
  --image=$IMAGE \
  --region=$REGION \
  --use-http2 \
  --set-env-vars=ENABLE_HTTP=0,ENABLE_GRPC=1,GRPC_PORT=8080,DEVICE=cuda \
  --set-env-vars=TAGGER_DEFAULT_CUTOFF=0.35 \
  --gpu=1 --gpu-type=nvidia-tesla-t4 \
  --memory=16Gi --cpu=4 \
  --allow-unauthenticated
```
Alternatively apply `AI/deploy/cloudrun-service.yaml` after replacing `PROJECT_ID` and `REGION` tokens:
```bash
envsubst < AI/deploy/cloudrun-service.yaml | gcloud run services replace -n teledeck-ai --region=$REGION -
```

*Expose the HTTP API via a second Cloud Run service* by setting `ENABLE_GRPC=0`, `HTTP_PORT=8080`, and reusing the same container image.

## 6. Deploy to GKE (HTTP + gRPC)
```bash
CLUSTER=teledeck-ai-cluster
REGION=us-central1

# Create a GPU-enabled standard cluster (Autopilot currently lacks stable GPU support)
gcloud container clusters create $CLUSTER \
  --region $REGION \
  --machine-type g2-standard-4 \
  --accelerator type=nvidia-tesla-t4,count=1 \
  --num-nodes 1

gcloud container clusters get-credentials $CLUSTER --region $REGION

# Install NVIDIA drivers on the node pool
kubectl apply -f https://raw.githubusercontent.com/GoogleCloudPlatform/container-engine-accelerators/master/daemonset.yaml

# Apply manifests (edit PROJECT_ID/REGION placeholders first)
kubectl apply -f AI/deploy/kubernetes/deployment.yaml
kubectl apply -f AI/deploy/kubernetes/service.yaml
```
Expose the LoadBalancer address and reach the REST endpoint on port 80 and gRPC on port 9090 once the external IP is provisioned.

## 7. Runtime Notes
- `MODEL_ROOT` defaults to `/app/models`. Mount a persistent volume or bake updated checkpoints into the image if retraining.
- Use `ENABLE_HTTP`/`ENABLE_GRPC` to trim unused protocols.
- Tagger thresholds can be tuned via `TAGGER_DEFAULT_CUTOFF` (applies when client omits a cutoff).
- Request timeout for remote URLs defaults to 15 seconds; override with `REQUEST_TIMEOUT_SECONDS`.

## 8. Observability & Health
- HTTP health probe: `GET /health` (returns `{"status":"ok"}`).
- gRPC health can be monitored through application logs; add gRPC health checking if integrating with service mesh.
- Enable Cloud Logging by attaching a sidecar or reading stdout/stderr (default behaviour in both Cloud Run and GKE).

The service is now production-ready: FastAPI + gRPC interfaces share a unified model container, configurable through environment variables, and the repository includes deployment manifests for Cloud Run and GKE.
