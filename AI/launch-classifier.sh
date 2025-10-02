#!/usr/bin/env bash
set -euo pipefail

REGION=${REGION:-us-central1}
REPO=${REPO:-teledeck}
IMAGE=${IMAGE:-ai-service}
TAG=${TAG:-v1}
SERVICE=${SERVICE:-teledeck-ai-grpc}
PROJECT_ID=${PROJECT_ID:-$(gcloud config get-value project 2> /dev/null)}

if [[ -z "${PROJECT_ID}" ]]; then
  echo "PROJECT_ID not set and gcloud project not configured." >&2
  exit 1
fi

FULL_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${IMAGE}:${TAG}"

if ! gcloud artifacts repositories describe "${REPO}" --location "${REGION}" >/dev/null 2>&1; then
  echo "Creating Artifact Registry repository ${REPO} in ${REGION}"
  gcloud artifacts repositories create "${REPO}" \
    --repository-format=docker \
    --location="${REGION}" \
    --description="Teledeck AI images"
fi

gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

echo "Building container image ${FULL_IMAGE}"
docker build -f AI/Dockerfile -t "${FULL_IMAGE}" AI

echo "Pushing container image"
docker push "${FULL_IMAGE}"

echo "Deploying Cloud Run service ${SERVICE} (gRPC, GPU)"
gcloud run deploy "${SERVICE}" \
  --image="${FULL_IMAGE}" \
  --region="${REGION}" \
  --use-http2 \
  --gpu=1 --gpu-type=nvidia-tesla-t4 \
  --memory=16Gi --cpu=4 \
  --set-env-vars=ENABLE_HTTP=0,ENABLE_GRPC=1,GRPC_PORT=8080,DEVICE=cuda \
  --allow-unauthenticated

echo "Deployment complete."
