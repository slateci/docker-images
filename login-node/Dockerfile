# syntax=docker/dockerfile:1
FROM centos:7

# Labels
LABEL io.slateci.image.name="login-node"
LABEL io.slateci.image.tags=""
LABEL org.opencontainers.image.authors="nlingareddy@uchicago.edu"
LABEL org.opencontainers.image.description=""
LABEL org.opencontainers.image.licenses="Unlicense"
LABEL org.opencontainers.image.title="Login Node"
LABEL org.opencontainers.image.url="https://github.com/slateci/docker-images"
LABEL org.opencontainers.image.vendor="SLATECI"
LABEL org.opencontainers.image.version="1.0.2"

RUN yum update -y

RUN yum install -y epel-release

RUN \
  yum install -y openssh-server pwgen supervisor authconfig
  
RUN yum install openssl -y \
    yum install -y openldap-clients pam_ldap nss-pam-ldap authconfig 

RUN \
  echo > /etc/sysconfig/i18n

# Clean up after yum:
RUN yum clean all && rm -rf /var/cache/yum

COPY container-files /

ENTRYPOINT ["/config/bootstrap.sh"]
