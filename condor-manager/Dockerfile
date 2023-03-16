# syntax=docker/dockerfile:1
#FROM opensciencegrid/software-base:fresh
FROM htcondor/cm:lts-el8

# Labels
LABEL io.slateci.image.name="condor-manager"
LABEL io.slateci.image.tags=""
LABEL org.opencontainers.image.authors="lincolnb@uchicago.edu"
LABEL org.opencontainers.image.description=""
LABEL org.opencontainers.image.licenses="Unlicense"
LABEL org.opencontainers.image.title="Condor Manager"
LABEL org.opencontainers.image.url="https://github.com/slateci/docker-images"
LABEL org.opencontainers.image.vendor="SLATECI"
LABEL org.opencontainers.image.version="10.0.2"

RUN yum update -y && yum install -y epel-release && yum install -y https://repo.opensciencegrid.org/osg/3.6/osg-3.6-el8-release-latest.rpm

# upcoming for tokens
RUN yum install -y pwgen \
  supervisor \
  openssl \
# commenting this out b\c it's not in the osg repo
# gratia-probe-glideinwms \ 
  gratia-probe-common \
  gratia-probe-condor \
  python3-scitokens-credmon \
  osg-ca-certs \
  glibc-static \
  wget \ 
  curl

RUN yum clean all && rm -rf /tmp/yum*

COPY container-files /
ENTRYPOINT  ["/usr/bin/supervisord", "-c", "/etc/supervisord.conf" ]
