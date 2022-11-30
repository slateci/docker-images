#!/bin/bash

# Enable strict mode:
set -euo pipefail

# Script variables:
export AWS_SDK_VERSION="${1}"
export OS_DISTRIBUTION="${2}"

cd /tmp
echo "Downloading AWS C++ SDK version: ${AWS_SDK_VERSION}..."
curl -LO https://slateci.io/slate-client-server/aws-cpp-sdk/${OS_DISTRIBUTION}-${AWS_SDK_VERSION}.tar.gz

echo "Installing AWS C++ SDK..."
tar -zxf ${OS_DISTRIBUTION}-${AWS_SDK_VERSION}.tar.gz --directory .
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
rm /tmp/${OS_DISTRIBUTION}-${AWS_SDK_VERSION}.tar.gz
