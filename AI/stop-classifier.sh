#!/bin/bash

# Delete the Cloud Run service
gcloud run services delete classifier-service --platform gke \
    --cluster classifier-cluster --cluster-location us-central1-a

# Delete the GKE cluster
gcloud container clusters delete classifier-cluster --zone us-central1-a --quiet

echo "Cluster and service deleted successfully."