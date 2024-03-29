# syntax=docker/dockerfile:1
FROM rockylinux:9

# Labels
LABEL io.slateci.image.name="slate-client-server"
LABEL io.slateci.image.tags=""
LABEL org.opencontainers.image.authors="adam.h.griffith@utah.edu,suchandra.thapa@gmail.com"
LABEL org.opencontainers.image.description="This is the container that pre-installs and builds all C++ dependencies, Helm3, and the AWS CLI into the file system of the resulting Centos7 image for the slateci/slate-client-server project."
LABEL org.opencontainers.image.licenses="Unlicense"
LABEL org.opencontainers.image.title="SLATE API Server Builtime & Runtime Environment"
LABEL org.opencontainers.image.url="https://github.com/slateci/slate-client-server"
LABEL org.opencontainers.image.vendor="SLATECI"
LABEL org.opencontainers.image.version="2.2.1"

# Docker image build arguments:
ARG awssdkversion=1.9.365
ARG helmversion=3.8.1
ARG javaversion=1.8.0
ARG kubectlversion=1.24.7
ARG opentelemetryversion=1.6.1

# Set up custom yum repos:
COPY ./resources/yum.repos.d/* /etc/yum.repos.d

# Package installs/updates:
RUN dnf install -y dnf-plugins-core && \
    dnf config-manager --set-enabled crb -y && \
    dnf install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm \
    https://dl.fedoraproject.org/pub/epel/epel-next-release-latest-9.noarch.rpm
RUN dnf install -y --allowerasing \
    libcurl \
    libcurl-devel
RUN dnf install -y boost-devel \
    ccache \
    cmake3 \
    cryptopp \
    gcc-c++.x86_64 \
    git \
    gmock \
    gmock-devel \
    google-benchmark \
    google-benchmark-devel \
    gpg \
    gtest \
    gtest-devel \
    json-devel \
    java-${javaversion} \
    kubectl-${kubectlversion} \
    make \
    openssl \
    openssl-devel \
    perl-Digest-SHA \
    procps-ng \
    protobuf-devel \
    protobuf-compiler \
    strace \
    unzip \
    which \
    yaml-cpp-devel \
    zlib-devel

# Package cache cleanup:
RUN dnf clean all && \
    rm -rf /var/cache/yum

# Set up scripts:
COPY ./scripts /tmp/scripts

# Install AWS C++ SDK
RUN chmod +x /tmp/scripts/install-aws-cpp-sdk.sh && \
    . /tmp/scripts/install-aws-cpp-sdk.sh ${awssdkversion} rocky9

# Install AWS CLI (for debugging):
COPY ./resources/aws/cli/public.key /tmp/aws-cli.key
RUN chmod +x /tmp/scripts/install-aws-cli.sh && \
    . /tmp/scripts/install-aws-cli.sh /tmp/aws-cli.key

# Install DynamoDB (for testing):
RUN chmod +x /tmp/scripts/install-dynamo.sh && \
    mkdir /dynamodb && \
    . /tmp/scripts/install-dynamo.sh /dynamodb

# Install opentelemetry-cpp
RUN chmod +x /tmp/scripts/install-opentelemetry.sh && \
    . /tmp/scripts/install-opentelemetry.sh ${opentelemetryversion} rocky9

# Install Helm3:
RUN chmod +x /tmp/scripts/install-helm.sh && \
    . /tmp/scripts/install-helm.sh ${helmversion}

# Clean up scripts:
RUN rm -rf /tmp/scripts
