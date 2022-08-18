# syntax=docker/dockerfile:1
FROM joyzoursky/python-chromedriver:3.9-alpine-selenium

# Labels
LABEL io.slateci.image.name="python-chromedriver-selenium"
LABEL io.slateci.image.tags="3.9-alpine"
LABEL org.opencontainers.image.authors="adam.h.griffith@utah.edu"
LABEL org.opencontainers.image.description="This is generalized container meant to support Selenium Python bindings and chromedriver."
LABEL org.opencontainers.image.licenses="Unlicense"
LABEL org.opencontainers.image.title="Selenium on Alpine"
LABEL org.opencontainers.image.url="https://hub.docker.com/r/joyzoursky/python-chromedriver/"
LABEL org.opencontainers.image.vendor="SLATECI"
LABEL org.opencontainers.image.version="1.0.2"

# Docker container environmental variables:
ENV SCREENSHOTS=1

# Package installs/updates:
RUN apk add git \
    which -f

# Install Python dependencies:
COPY ./requirements.txt ./
RUN pip3 install -r ./requirements.txt && \
    rm ./requirements.txt

# Set the project directory:
RUN mkdir /opt/project

# Set the work directory:
WORKDIR /opt/project

# Volumes
VOLUME [ "/opt/project" ]
