# syntax=docker/dockerfile:1
FROM rucio/rucio-clients:release-1.31.4

# Labels
LABEL io.slateci.image.name="atlas-xcache-heartbeats"
LABEL io.slateci.image.tags=""
LABEL org.opencontainers.image.authors=""
LABEL org.opencontainers.image.description="This is a container meant to provide a heartbeat for Atlas XCache."
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.title="atlas-xcache-heartbeats"
LABEL org.opencontainers.image.url="https://github.com/slateci/docker-images"
LABEL org.opencontainers.image.vendor="SLATECI"
LABEL org.opencontainers.image.version="1.0.0"

USER 0:0

COPY run_heartbeats.sh /usr/local/sbin/
COPY heartbeat.py /usr/local/sbin/
COPY rucio.cfg ca.crt /opt/rucio/etc/

ENV CERTPATH=/etc/grid-certs
ENV X509_USER_PROXY=/etc/proxy/x509up
ENV RUCIO_AUTH_TYPE=x509_proxy
ENV RUCIO_ACCOUNT=ivukotic

CMD [ "/usr/local/sbin/run_heartbeats.sh" ]