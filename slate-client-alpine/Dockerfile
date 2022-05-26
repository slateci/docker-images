# syntax=docker/dockerfile:1.4
FROM alpine:3.10

# Package installs/updates:
RUN apk update && \
    apk upgrade && \
    apk add \
        cmake \
        curl-dev \
        curl-static \
        gcc \
        g++ \
        libc-dev \
        libssh2-dev \
        make \
        musl-dev \
        nghttp2-dev \
        nghttp2-static \
        openssl-dev \
        zlib-dev
