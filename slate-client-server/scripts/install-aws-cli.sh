#!/bin/bash

# Enable strict mode:
set -euo pipefail

# Script variables:
export KEY_PATH="${1}"

cd /tmp
echo "Downloading latest AWS CLI..."
for FILENAME in awscli-exe-linux-x86_64.zip awscli-exe-linux-x86_64.zip.sig
  do
    curl -fsSL https://awscli.amazonaws.com/$FILENAME -o $FILENAME
  done

echo "Verifying download..."
gpg --import ${KEY_PATH}
gpg --verify awscli-exe-linux-x86_64.zip.sig awscli-exe-linux-x86_64.zip || exit 1

echo "Extracting download archive..."
unzip awscli-exe-linux-x86_64.zip

echo "Installing AWS CLI..."
./aws/install

echo "Cleaning up..."
rm ${KEY_PATH}
rm -rf /tmp/aws
rm /tmp/awscli*
