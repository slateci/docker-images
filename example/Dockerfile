# syntax=docker/dockerfile:1
FROM centos:7

# Labels
LABEL io.slateci.image.name="example"
LABEL io.slateci.image.tags="centos7"
LABEL org.opencontainers.image.authors="example@no-reply.com"
LABEL org.opencontainers.image.description="This is an example."
LABEL org.opencontainers.image.licenses="Unlicense"
LABEL org.opencontainers.image.title="Example Image"
LABEL org.opencontainers.image.url="https://github.com/slateci/docker-images"
LABEL org.opencontainers.image.vendor="SLATECI"
LABEL org.opencontainers.image.version="1.0.0"

RUN yum update -y && \
    yum install -y epel-release

CMD ["echo", "Hello World!"]
