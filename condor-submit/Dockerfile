# syntax=docker/dockerfile:1
FROM opensciencegrid/software-base:fresh

# Labels
LABEL io.slateci.image.name="condor-submit"
LABEL io.slateci.image.tags=""
LABEL org.opencontainers.image.authors="lincolnb@uchicago.edu"
LABEL org.opencontainers.image.description=""
LABEL org.opencontainers.image.licenses="Unlicense"
LABEL org.opencontainers.image.title="Condor Submit"
LABEL org.opencontainers.image.url="https://github.com/slateci/docker-images"
LABEL org.opencontainers.image.vendor="SLATECI"
LABEL org.opencontainers.image.version="1.0.2"

RUN yum update -y && yum install -y epel-release

# upcoming for tokens
RUN yum install -y --enablerepo=osg-upcoming \
  condor \
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
  python2-scitokens-credmon \
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

RUN authconfig --update --enablesssd --enablesssdauth --enablemkhomedir

# Make sure we have some needed dirs
RUN mkdir -p /etc/condor/passwords.d && \
    mkdir -p /etc/condor/tokens.d && \
    chown condor: /etc/condor/passwords.d && \
    chown condor: /etc/condor/tokens.d

CMD ["/usr/local/sbin/supervisord_startup.sh"]
