#!/bin/bash

# Enable strict mode:
set -euo pipefail

cat << EOF
===================================================
Helm/GCloud Utility Container
===================================================
EOF

# Set gcloud cli auth and configuration:
gcloud auth activate-service-account --key-file ${GOOGLE_APPLICATION_CREDENTIALS}
gcloud config set project ${GCLOUD_PROJECT}
gcloud config set compute/zone ${GCLOUD_COMPUTE_ZONE}
gcloud container clusters get-credentials ${GCLOUD_GKE_CLUSTER}

/bin/bash