# syntax=docker/dockerfile:1
FROM rockylinux:9

# Labels
LABEL io.slateci.image.name="slate-client-server"
LABEL io.slateci.image.tags=""
LABEL org.opencontainers.image.authors="adam.h.griffith@utah.edu"
LABEL org.opencontainers.image.description="This is the container that pre-installs and builds all C++ dependencies, Helm3, and the AWS CLI into the file system of the resulting Centos7 image for the slateci/slate-client-server project."
LABEL org.opencontainers.image.licenses="Unlicense"
LABEL org.opencontainers.image.title="SLATE API Server CentOS Build Environment"
LABEL org.opencontainers.image.url="https://github.com/slateci/slate-client-server"
LABEL org.opencontainers.image.vendor="SLATECI"
LABEL org.opencontainers.image.version="2.0.0"

# Docker image build arguments:
ARG awssdkversion=1.9.365
ARG helmversion=3.8.1
ARG javaversion=1.8.0
ARG kubectlversion=1.21.11

# Set up custom yum repos:
COPY ./resources/yum.repos.d/* /etc/yum.repos.d

# Package installs/updates:
RUN dnf install -y dnf-plugins-core && \
    dnf config-manager --set-enabled crb -y && \
    dnf install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm \
    https://dl.fedoraproject.org/pub/epel/epel-next-release-latest-9.noarch.rpm
RUN dnf install -y boost-devel \
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
    zlib-devel \
    git 

#RUN dnf clean all && rm -rf /var/cache/yum

# Install AWS C++ SDK
RUN mkdir /tmp/aws && \
    cd /tmp/aws && \
    git clone https://github.com/aws/aws-sdk-cpp.git && \
    cd aws-sdk-cpp && \
    git submodule update --init --recursive && \
    git checkout tags/$awssdkversion && \
    cd .. && \
    mkdir build && \
    cd build && \
    cmake ../aws-sdk-cpp  -DBUILD_ONLY="dynamodb;route53" -DBUILD_SHARED_LIBS=Off  -DCMAKE_PREFIX_PATH=/tmp/aws/aws-sdk-cpp -DENABLE_TESTING=Off && \
    make && \
    make install

# Set up scripts:
COPY ./scripts /tmp/scripts

# Install AWS C++ SDK
#RUN chmod +x /tmp/scripts/install-aws-cpp-sdk.sh && \
#    . /tmp/scripts/install-aws-cpp-sdk.sh ${awssdkversion} rocky9

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

