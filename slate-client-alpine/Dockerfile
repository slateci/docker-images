FROM alpine:3.10
#FROM alpine:3.6

RUN apk update && \
    apk upgrade && \
    apk --update add \
        gcc \
        g++ \
        build-base \
        cmake \
        bash \
        libstdc++ \
        curl-dev \
        zlib-dev \
        nghttp2-static && \
    rm -rf /var/cache/apk/*
