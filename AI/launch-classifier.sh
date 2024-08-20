#!/bin/bash

# Set your project ID
GCLOUD_PROJECT_ID=$(gcloud config get project)

# Create GKE cluster with GPU nodes
gcloud container clusters create classifier-cluster \
    --zone us-central1-a \
    --num-nodes 1 \
    --machine-type n1-standard-4 \
    --accelerator type=nvidia-tesla-t4,count=1

# Get credentials for the cluster
gcloud container clusters get-credentials classifier-cluster --zone us-central1-a

# Deploy to Cloud Run on GKE
gcloud run deploy classifier-service \
    --image gcr.io/${PROJECT_ID}/classifier-service:v1 \
    --platform gke \
    --cluster classifier-cluster \
    --cluster-location us-central1-a \
    --min-instances 0 \
    --max-instances 3 \
    --port 8080 \
    --use-http2 \
    --set-env-vars="CUDA_VISIBLE_DEVICES=0"

echo "Classifier deployed successfully."