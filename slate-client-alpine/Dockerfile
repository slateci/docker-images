# syntax=docker/dockerfile:1.4
FROM alpine:3.16.0

# Docker image build arguments:
ARG versionoverride="X.Y.Z"

# Docker container environmental variables:
ENV VERSION_OVERRIDE=${versionoverride}

# Package installs/updates:
RUN apk add --no-cache \
    boost-dev \
    cmake \
    curl-dev \
    gcc \
    g++ \
    make \
    musl-dev \
    openssl-dev \
    zlib-dev
