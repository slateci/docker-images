FROM python:3.8-slim

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git=1:2.20.* && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt
RUN git clone https://github.com/kubernetes-sigs/kubespray.git -b v2.15.1

WORKDIR /opt/kubespray
RUN pip3 install --no-cache-dir -r requirements.txt && \
    rm -rf inventory

ENTRYPOINT ["ansible-playbook"]
