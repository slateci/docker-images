# syntax=docker/dockerfile:1
FROM minio/minio:latest

# Labels
LABEL io.slateci.image.name="minio"
LABEL io.slateci.image.tags="RELEASE.2020-09-10T22-02-45Z"
LABEL org.opencontainers.image.authors="dev@min.io"
LABEL org.opencontainers.image.description=""
LABEL org.opencontainers.image.licenses="Unlicense"
LABEL org.opencontainers.image.title="MinIO"
LABEL org.opencontainers.image.url="https://min.io"
LABEL org.opencontainers.image.vendor="MinIO"
LABEL org.opencontainers.image.version="1.0.2"

COPY dockerscripts/docker-entrypoint.sh /usr/bin/

ENTRYPOINT ["/usr/bin/docker-entrypoint.sh"]

VOLUME ["/data"]

CMD ["minio"]
