# syntax=docker/dockerfile:1
FROM alpine:3.11.6

# Labels
LABEL io.slateci.image.name="slate-client-alpine"
LABEL io.slateci.image.tags=""
LABEL org.opencontainers.image.authors="adam.h.griffith@utah.edu"
LABEL org.opencontainers.image.description="This is the container that provides a build environment for the slateci/slate-client-server project and the static Linux SLATE Remote Client."
LABEL org.opencontainers.image.licenses="Unlicense"
LABEL org.opencontainers.image.title="SLATE Remote Client Alpine Build Environment"
LABEL org.opencontainers.image.url="https://github.com/slateci/slate-client-server"
LABEL org.opencontainers.image.vendor="SLATECI"
LABEL org.opencontainers.image.version="1.3.0"

# Package installs/updates:
RUN apk update && \
    apk upgrade && \
    apk add --no-cache \
        ccache \
        cmake \
        curl-dev \
        curl-static \
        bash \
        gcc \
        g++ \
        libc-dev \
        libssh2-dev \
        make \
        musl-dev \
        nghttp2-dev \
        nghttp2-static \
        openssl-dev \
        openssl-libs-static \
        tar \
        zlib-dev \
        zlib-static
