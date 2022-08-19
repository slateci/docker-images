# syntax=docker/dockerfile:1
FROM opensciencegrid/software-base:fresh

# Labels
LABEL io.slateci.image.name="condor-manager"
LABEL io.slateci.image.tags=""
LABEL org.opencontainers.image.authors="lincolnb@uchicago.edu"
LABEL org.opencontainers.image.description=""
LABEL org.opencontainers.image.licenses="Unlicense"
LABEL org.opencontainers.image.title="Condor Manager"
LABEL org.opencontainers.image.url="https://github.com/slateci/docker-images"
LABEL org.opencontainers.image.vendor="SLATECI"
LABEL org.opencontainers.image.version="8.9.0"

RUN yum update -y && yum install -y epel-release

# upcoming for tokens
RUN yum install -y --enablerepo=osg-upcoming \
  condor \
  pwgen \
  supervisor \
  openssl \
  gratia-probe-glideinwms \ 
  gratia-probe-common \
  gratia-probe-condor \
  python2-scitokens-credmon \
  osg-ca-certs \
  glibc-static \
  wget \ 
  curl

RUN yum clean all && rm -rf /tmp/yum*

COPY container-files /

CMD ["/usr/local/sbin/supervisord_startup.sh"]
