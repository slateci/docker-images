# syntax=docker/dockerfile:1
FROM htcondor/submit:lts-el8

# Labels
LABEL io.slateci.image.name="condor-submit"
LABEL io.slateci.image.tags=""
LABEL org.opencontainers.image.authors="lincolnb@uchicago.edu"
LABEL org.opencontainers.image.description=""
LABEL org.opencontainers.image.licenses="Unlicense"
LABEL org.opencontainers.image.title="Condor Submit"
LABEL org.opencontainers.image.url="https://github.com/slateci/docker-images"
LABEL org.opencontainers.image.vendor="SLATECI"
LABEL org.opencontainers.image.version="2.0.0"

RUN yum update -y && yum install -y epel-release && \
    yum install -y https://repo.opensciencegrid.org/osg/3.6/osg-3.6-el8-release-latest.rpm

# upcoming for tokens
RUN yum install -y \
#removing b\c it's already in the upstream image we're using here
#  condor \
  openssh-server \
  authconfig \
  sssd \
  pwgen \
  supervisor \
  openssl \
  htop \ 
  gratia-probe-glideinwms \ 
  gratia-probe-common \
  gratia-probe-condor \
  emacs \ 
  vim-enhanced \
  nano \
  iotop \ 
  tmux \
  screen \
  zsh \
  tcsh \
  git \
  subversion \
  tcl \
  jq \
  python3-scitokens-credmon \
  stashcache-client \
  pegasus \
  @development \
  xorg-x11-xauth \
  xorg-x11-apps \
  bc \
  glibc-static \
  wget \ 
  curl

# Clean up after yum:
RUN yum clean all && rm -rf /var/cache/yum

COPY container-files /

#Temporarily commented out as it starting those services gives some errors -MA 3/24/23
#RUN authconfig --update --enablesssd --enablesssdauth --enablemkhomedir

# Make sure we have some needed dirs
RUN mkdir -p /etc/condor/passwords.d && \
    mkdir -p /etc/condor/tokens.d && \
    chown condor: /etc/condor/passwords.d && \
    chown condor: /etc/condor/tokens.d

CMD ["/usr/local/sbin/supervisord_startup.sh"]

