# syntax=docker/dockerfile:1

# Docker image build arguments:
ARG awssdkversion=1.7.345
ARG helmversion=3.8.1
ARG javaversion=1.8.0
ARG kubectlversion=1.21.11

######################################
# Build Stage                        #
######################################
FROM centos:7 as build-stage

# Docker image build arguments:
ARG awssdkversion

# Package installs/updates:
RUN yum install epel-release -y
RUN yum install boost-devel \
    cmake3 \
    gcc-c++.x86_64 \
    git \
    libcurl-devel \
    make \
    openssl-devel \
    yaml-cpp-devel \
    zlib-devel -y

# Download AWS C++ SDK
RUN curl -LO https://github.com/aws/aws-sdk-cpp/archive/${awssdkversion}.tar.gz && \
    tar xzf ${awssdkversion}.tar.gz

# Change working directory:
WORKDIR /build

# Build AWS C++ SDK
RUN cmake3 ../aws-sdk-cpp-${awssdkversion} -DBUILD_ONLY="dynamodb;route53" -DBUILD_SHARED_LIBS=Off && \
    make

#######################################
## Final Stage                        #
#######################################
FROM centos:7 as final-stage

# Docker image build arguments:
ARG awssdkversion
ARG helmversion
ARG kubectlversion

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
COPY --from=build-stage /aws-sdk-cpp-${awssdkversion} /aws-sdk-cpp-${awssdkversion}
COPY --from=build-stage /build /build
RUN cd ./build && \
    make install

# Set up scripts:
COPY ./scripts /tmp/scripts

# Install AWS CLI (for debugging)
RUN chmod +x /tmp/scripts/install-aws-cli.sh && \
    . /tmp/scripts/install-aws-cli.sh

# Install Helm3:
RUN chmod +x /tmp/scripts/install-helm.sh && \
    . /tmp/scripts/install-helm.sh ${helmversion}

# Clean up scripts:
RUN rm -rf /tmp/scripts
