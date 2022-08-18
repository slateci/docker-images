# syntax=docker/dockerfile:1
FROM centos:7

# Labels
LABEL io.slateci.image.name="slate-client-server"
LABEL io.slateci.image.tags=""
LABEL org.opencontainers.image.authors="adam.h.griffith@utah.edu"
LABEL org.opencontainers.image.description="This is the container that pre-installs and builds all C++ dependencies, Helm3, and the AWS CLI into the file system of the resulting Centos7 image for the slateci/slate-client-server project."
LABEL org.opencontainers.image.licenses="Unlicense"
LABEL org.opencontainers.image.title="SLATE API Server CentOS Build Environment"
LABEL org.opencontainers.image.url="https://github.com/slateci/slate-client-server"
LABEL org.opencontainers.image.vendor="SLATECI"
LABEL org.opencontainers.image.version="1.0.9"

# Docker image build arguments:
ARG awssdkversion=1.7.345
ARG helmversion=3.8.1
ARG javaversion=1.8.0
ARG kubectlversion=1.21.11

# Set up custom yum repos:
COPY ./resources/yum.repos.d/* /etc/yum.repos.d

# Package installs/updates:
RUN yum install epel-release -y
RUN yum install boost-devel \
    cmake3 \
    gcc-c++.x86_64 \
    libcurl-devel \
    java-${javaversion} \
    kubectl-${kubectlversion} \
    make \
    openssl-devel \
    perl-Digest-SHA \
    unzip \
    which \
    yaml-cpp-devel \
    zlib-devel -y \
RUN yum clean all && rm -rf /var/cache/yum

# Install AWS C++ SDK
RUN  mkdir -p /__w/slate-client-server/slate-client-server/ && \
     cd /__w/slate-client-server/slate-client-server/ && \
     curl -fsSL https://slateci.io/slate-client-server/aws-cpp-sdk/centos7-${awssdkversion}.tar.gz -o centos7-${awssdkversion}.tar.gz && \
     tar -zxf centos7-${awssdkversion}.tar.gz --directory . && \
     cd ./aws/build && \
     make install

# Set up scripts:
COPY ./scripts /tmp/scripts

# Install AWS CLI (for debugging):
RUN chmod +x /tmp/scripts/install-aws-cli.sh && \
    . /tmp/scripts/install-aws-cli.sh

# Install DynamoDB (for testing):
RUN chmod +x /tmp/scripts/install-dynamo.sh && \
    mkdir /dynamodb && \
    . /tmp/scripts/install-dynamo.sh /dynamodb

# Install Helm3:
RUN chmod +x /tmp/scripts/install-helm.sh && \
    . /tmp/scripts/install-helm.sh ${helmversion}

# Clean up scripts:
RUN rm -rf /tmp/scripts
