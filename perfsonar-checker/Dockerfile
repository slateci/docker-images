# syntax=docker/dockerfile:1
FROM perfsonar/testpoint:v4.3.4

# Docker image labels:
LABEL maintainer="SLATE Team"

# Copy additional resources:
COPY run-perfsonar-tests.sh /usr/local/bin/run-perfsonar-tests.sh
COPY supervisord.conf /etc/supervisord.conf

# Run once the container has started:
CMD /usr/bin/supervisord -c /etc/supervisord.conf
