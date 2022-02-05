# syntax=docker/dockerfile:1
FROM joyzoursky/python-chromedriver:3.9-alpine-selenium

# Docker container environmental variables:
ENV SCREENSHOTS=1

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
