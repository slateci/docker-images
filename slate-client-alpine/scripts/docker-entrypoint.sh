#!/bin/sh

# Enable strict mode:
set -euo pipefail

echo "Building slate binary..."
cd "/slate/build"
cmake .. -DBUILD_CLIENT=True -DBUILD_SERVER=False -DBUILD_SERVER_TESTS=False -DSTATIC_CLIENT=True
make -k

/bin/sh