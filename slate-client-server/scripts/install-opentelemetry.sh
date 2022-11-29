#!/bin/bash

# Enable strict mode:
set -euo pipefail

# Script variables:
export OTEL_CLIENT_VERSION="${1}"
export OS_DISTRIBUTION="${2}"

cd /tmp
echo "Downloading OpenTelemetry C++ client version: ${OTEL_CLIENT_VERSION}..."
curl -LO https://slateci.io/slate-client-server/opentelemetry-cpp/${OS_DISTRIBUTION}-${OTEL_CLIENT_VERSION}.tar.gz

echo "Installing OpenTelemetry C++ client..."
tar -zxf ${OS_DISTRIBUTION}-${OTEL_CLIENT_VERSION}.tar.gz --directory .
chmod -R 755 /tmp/install-artifacts
ls -al /tmp/install-artifacts

echo "Copying installation artifacts to /usr/local/**..."
ID_LIKE=$(awk -F= '$1=="ID_LIKE" { print $2 ;}' /etc/os-release)
if [[ "${ID_LIKE}" ==  *"debian"* ]]
then
  cp -rf ./install-artifacts/lib/** /usr/local/lib/
else
  cp -rf ./install-artifacts/lib64/** /usr/local/lib64/
fi
cp -rf ./install-artifacts/include/** /usr/local/include/

echo "Cleaning up..."
rm -rf /tmp/install-artifacts
