#!/bin/bash

# Enable strict mode:
set -euo pipefail

# Script variables:
export VALS_VERSION="${1}"

cd /tmp
echo "Downloading vals version: ${VALS_VERSION}..."
curl -LO https://github.com/variantdev/vals/releases/download/v${VALS_VERSION}/vals_${VALS_VERSION}_linux_amd64.tar.gz
curl -LO https://github.com/variantdev/vals/releases/download/v${VALS_VERSION}/vals_${VALS_VERSION}_checksums.txt

echo "Verifying download..."
echo $(cat vals_${VALS_VERSION}_checksums.txt | grep .*vals_${VALS_VERSION}_linux_amd64.tar.gz) > checksum.txt
sha256sum -c checksum.txt || exit 1

echo "Installing vals..."
tar xzf vals_${VALS_VERSION}_linux_amd64.tar.gz
mv vals /usr/local/bin

echo "Cleaning up..."
rm vals_${VALS_VERSION}_linux_amd64.tar.gz vals_${VALS_VERSION}_checksums.txt checksum.txt
