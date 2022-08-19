# syntax=docker/dockerfile:1
FROM perfsonar/testpoint:v4.3.4

# Labels
LABEL io.slateci.image.name="perfsonar-checker"
LABEL io.slateci.image.tags=""
LABEL org.opencontainers.image.authors=""
LABEL org.opencontainers.image.description=""
LABEL org.opencontainers.image.licenses="Unlicense"
LABEL org.opencontainers.image.title="perfSONAR Checker"
LABEL org.opencontainers.image.url="https://github.com/slateci/docker-images"
LABEL org.opencontainers.image.vendor="SLATECI"
LABEL org.opencontainers.image.version="4.3.4"

#ADD run-my-tests.sh /usr/local/bin/run-my-tests.sh
ADD run-perfsonar-tests.sh /usr/local/bin/run-perfsonar-tests.sh
ADD supervisord.conf /etc/supervisord.conf
CMD /usr/bin/supervisord -c /etc/supervisord.conf
