# CLion remote docker environment (How to build docker container, run and stop it)
#
# Build and run:
#   docker build -t clion/centos7-cpp-env:0.1 -f Dockerfile.centos7-cpp-env .
#   docker run -d --cap-add sys_ptrace -p127.0.0.1:2222:22 clion/centos7-cpp-env:0.1
#   ssh-keygen -f "$HOME/.ssh/known_hosts" -R "[localhost]:2222"
#
# stop:
#   docker stop clion_remote_env
#
# ssh credentials (test user):
#   user@password

LABEL io.slateci.image.name="slate-server-development"
LABEL io.slateci.image.tags=""
LABEL org.opencontainers.image.authors="suchandra.thapa@gmail.com"
LABEL org.opencontainers.image.description="This is the container that pre-installs and builds all C++ dependencies, Helm3, and the AWS CLI into an image that can be used to develop the slate-client-server"
LABEL org.opencontainers.image.licenses="Unlicense"
LABEL org.opencontainers.image.title="SLATE API Server Development Environment"
LABEL org.opencontainers.image.url="https://github.com/slateci/docker-images"
LABEL org.opencontainers.image.vendor="SLATECI"
LABEL org.opencontainers.image.version="1.0.0"



ARG baseimage=hub.opensciencegrid.org/slate/slate-client-server:2.1.0
ARG port=18080
FROM ${baseimage} as local-stage

# Docker image build arguments:
ARG awssdkversion=1.9.365


# Docker image build arguments:
ARG port

# Docker container environmental variables:
ENV VERSION_OVERRIDE="localdev"

# Ports:
EXPOSE ${port}

# Volumes:
VOLUME [ "/slate" ]

# Run once the container has started:
ENTRYPOINT [ "/bin/bash" ]

#######################################
## Build Stage                        #
#######################################
FROM ${baseimage} as build-stage

# Docker image build arguments:
ARG versionoverride="X.Y.Z"
ARG sshpassword="password"

# Docker container environmental variables:
ENV VERSION_OVERRIDE=${versionoverride}
ENV SSH_PASSWORD_OVERRIDE=${sshpassword}

RUN dnf -y update \
 && dnf -y install openssh-server \
  make \
  autoconf \
  automake \
  dos2unix \
  ninja-build \
  gcc \
  gcc-c++ \
  gdb \
  clang \
  cmake \
  rsync \
  tar \
  passwd \
  python \
  boost \
  boost-devel \
  groff \
  less \
  which \
  cmake3 \
  zlib-devel \
  zlib \
  yaml-cpp\
  yaml-cpp-devel \
  openssl \
  openssl-devel \
  libcurl-devel \
  libcurl \
  cryptopp \
  strace \
  procps-ng \
  json-devel \
  protobuf-devel \
  protobuf-compiler \
  gmock \
  gmock-devel \
  gtest \
  gtest-devel \
  google-benchmark \
  google-benchmark-devel \
  perf \
  valgrind \
  valgrind-devel \
  && dnf clean all

# Install AWS CLI
RUN ln -s /usr/local/aws-cli/v2/current/bin/aws aws && \
    ln -s /usr/local/aws-cli/v2/current/bin/aws_completer aws_completer


# Install DynamoDB locally
RUN cd /tmp && \
    curl  https://s3.us-west-2.amazonaws.com/dynamodb-local/dynamodb_local_latest.tar.gz -o  db.tar.gz && \
    tar xvzf db.tar.gz && \
    rm db.tar.gz

# Set kernel
RUN ssh-keygen -A

RUN ( \
    echo 'LogLevel DEBUG2'; \
    echo 'PermitRootLogin yes'; \
    echo 'PasswordAuthentication yes'; \
    echo 'Subsystem sftp /usr/libexec/openssh/sftp-server'; \
  ) > /etc/ssh/sshd_config_test_clion

RUN useradd -m clionremote \
  && yes $SSH_PASSWORD_OVERRIDE | passwd clionremote

CMD ["/usr/sbin/sshd", "-D", "-e", "-f", "/etc/ssh/sshd_config_test_clion"]
