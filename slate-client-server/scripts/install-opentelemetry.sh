#!/bin/bash

# Enable strict mode:
set -euo pipefail

# Script variables:
export OTEL_CLIENT_VERSION="${1}"

mkdir /tmp/opentelemetry
cd /tmp/opentelemetry
echo "Downloading OpenTelemetry C++ client version: ${OTEL_CLIENT_VERSION}..."
curl -fsSL https://github.com/open-telemetry/opentelemetry-cpp/archive/refs/tags/v${OTEL_CLIENT_VERSION}.tar.gz -o v${OTEL_CLIENT_VERSION}.tar.gz

echo "Installing OpenTelemetry C++ client..."
tar -zxf v${OTEL_CLIENT_VERSION}.tar.gz
ls -al
mkdir ./build
cd ./build
cmake ../opentelemetry-cpp-${OTEL_CLIENT_VERSION} \
      -DWITH_OTLP=ON
make
make install

echo "Cleaning up..."
rm -rf /tmp/opentelemetry
