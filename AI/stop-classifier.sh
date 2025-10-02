#!/usr/bin/env bash
set -euo pipefail

SERVICE=${SERVICE:-teledeck-ai-grpc}
REGION=${REGION:-us-central1}
DELETE_CLUSTER=${DELETE_CLUSTER:-0}
CLUSTER=${CLUSTER:-teledeck-ai-cluster}

if gcloud run services describe "${SERVICE}" --region "${REGION}" >/dev/null 2>&1; then
  echo "Deleting Cloud Run service ${SERVICE} in ${REGION}"
  gcloud run services delete "${SERVICE}" --region "${REGION}" --quiet
else
  echo "Cloud Run service ${SERVICE} not found; skipping"
fi

if [[ "${DELETE_CLUSTER}" == "1" ]]; then
  echo "Deleting GKE cluster ${CLUSTER} in ${REGION}"
  gcloud container clusters delete "${CLUSTER}" --region "${REGION}" --quiet || true
fi

echo "Teardown complete."
