ARG PYTHON_VERSION="3.10"
FROM python:${PYTHON_VERSION}

LABEL io.slateci.image.name="globus-compute"
LABEL io.slateci.image.tags=""
LABEL org.opencontainers.image.authors="jason.stidd@utah.edu"
LABEL org.opencontainers.image.description="Globus Compute"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.title="Globus Compute"
LABEL org.opencontainers.image.url="https://github.com/slateci/docker-images"
LABEL org.opencontainers.image.vendor="SLATECI"
LABEL org.opencontainers.image.version="0.0.1"

# Build args for speeding up development for those of us on crappy inet connections
# i.e., $ docker build ... --build-arg ... --build-arg ...
# something like: http://cache.fqdn:3142
ARG apt_proxy_url

# something like: [global]\nindex-url = ...
ARG pip_conf

RUN if [ -n "$apt_proxy_url" ]; then echo "Acquire::http { Proxy \"$apt_proxy_url\"; };" > /etc/apt/apt.conf.d/01proxy; fi
RUN apt-get update && apt-get upgrade -y

RUN if [ -n "$pip_conf" ]; then echo "$pip_conf" > "/etc/pip.conf"; fi

RUN python -m pip install -U pip
RUN python -m pip install kubernetes
RUN python -m pip install --no-binary :all: --force-reinstall pyzmq

RUN mkdir /opt/compute
COPY compute_sdk /opt/compute/compute_sdk/
COPY compute_endpoint /opt/compute/compute_endpoint/
WORKDIR /opt/compute/
RUN python -m pip install compute_endpoint/ compute_sdk/
RUN rm -rf /opt/compute/

# Undo local-dev ministrations
RUN if [ -n "$pip_conf" ]; then rm -f "/etc/pip.conf"; fi
RUN if [ -n "$apt_proxy_url" ]; then rm -f "/etc/apt/apt.conf.d/01proxy"; fi

RUN useradd -m compute
RUN mkdir -p /home/compute/.kube
USER compute
WORKDIR /home/compute
COPY helm/boot.sh .
COPY helm/bashrc ./.bashrc
ENV HOME /home/compute
