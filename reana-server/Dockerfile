FROM reanahub/reana-server:0.9.0

LABEL io.slateci.image.name="Reana Server"
LABEL io.slateci.image.tags=""
LABEL org.opencontainers.image.authors=""
LABEL org.opencontainers.image.description="Reana Platform - Reana Server (rest-api)"
LABEL org.opencontainers.image.licenses="Unlicense"
LABEL org.opencontainers.image.title="Reana Server"
LABEL org.opencontainers.image.url="https://github.com/slateci/docker-images"
LABEL org.opencontainers.image.vendor="SLATECI"
#This is just an image version that should be incremented everytime the image is updated
LABEL org.opencontainers.image.version="0.0.1"
LABEL maintainer="SLATE Team"

RUN apt-get update -y
RUN apt-get install --no-install-recommends -y \
	supervisor && \
	apt-get autoremove -y && \
    	apt-get clean && \
    	rm -rf /var/lib/apt/lists/*
RUN mkdir -p /var/log/supervisor
#COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

CMD ["/usr/bin/supervisord"]
