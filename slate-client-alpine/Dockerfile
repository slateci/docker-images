# syntax=docker/dockerfile:1.4
FROM alpine:3.10.9

# Package installs/updates:
RUN apk update && \
    apk upgrade && \
    apk add --no-cache \
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


# For alpine:3.16.0:
# * Add openssl-libs-static to apk
# * Need to find static library for:
#   `/usr/lib/gcc/x86_64-alpine-linux-musl/11.2.1/../../../../x86_64-alpine-linux-musl/bin/ld: cannot find -lz: No such file or directory`