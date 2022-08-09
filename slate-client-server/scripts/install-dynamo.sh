#!/bin/bash

# Enable strict mode:
set -euo pipefail

# Script variables:
export INSTALL_PATH="${1}"

cd "/tmp"
echo "Downloading latest DynamoDB from Amazon..."
for FILENAME in dynamodb_local_latest.tar.gz dynamodb_local_latest.tar.gz.sha256
  do
    curl -fsSL https://s3.us-west-2.amazonaws.com/dynamodb-local/$FILENAME -o $FILENAME
  done

echo "Verifying download..."
sha256sum -c dynamodb_local_latest.tar.gz.sha256 || exit 1

echo "Extracting download archive..."
tar -zxf dynamodb_local_latest.tar.gz --directory ${INSTALL_PATH}

echo "Cleaning up..."
rm /tmp/dynamodb_local_latest*
