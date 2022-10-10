# syntax=docker/dockerfile:1

# Docker image build arguments:
ARG googlecloudsdkversion=405.0.0
ARG helmplugindiffversion=3.6.0
ARG helmpluginsecretsversion=4.1.1
ARG helmversion=3.8.1
ARG varsversion=0.18.0

# Base image:
FROM docker.io/google/cloud-sdk:${googlecloudsdkversion}

# Labels:
LABEL io.slateci.image.name="helm-gcloud-sdk"
LABEL io.slateci.image.tags=""
LABEL org.opencontainers.image.authors="adam.h.griffith@utah.edu"
LABEL org.opencontainers.image.description="This is the container for Helm and the Google Cloud SDK."
LABEL org.opencontainers.image.licenses="Unlicense"
LABEL org.opencontainers.image.title="Helm & Google Cloud SDK"
LABEL org.opencontainers.image.url="https://github.com/slateci/docker-images/helm-gcloud-sdk"
LABEL org.opencontainers.image.vendor="SLATECI"
LABEL org.opencontainers.image.version="1.0.1"

# Change working directory:
WORKDIR /tmp

# Install Helm3:
RUN curl -LO https://raw.githubusercontent.com/slateci/docker-images/master/slate-client-server/scripts/install-helm.sh
RUN chmod +x ./install-helm.sh && \
    ./install-helm.sh ${helmversion} && \
    rm ./install-helm.sh

# Install Helm Plugins
RUN helm plugin install https://github.com/databus23/helm-diff --version ${helmplugindiffversion} && \
    helm plugin install https://github.com/jkroepke/helm-secrets --version ${helmpluginsecretsversion}

# Install vals
COPY ./scripts/install-vals.sh ./
RUN chmod +x ./install-vals.sh && \
    ./install-vals.sh ${varsversion} && \
    rm ./install-vals.sh

# Change working directory:
WORKDIR /

# Prepare entrypoint:
COPY ./scripts/docker-entrypoint.sh ./
RUN chmod +x ./docker-entrypoint.sh

# Change working directory:
WORKDIR /work

# Volumes:
VOLUME /work

# Run once the container has started:
ENTRYPOINT [ "/docker-entrypoint.sh" ]