# syntax=docker/dockerfile:1
FROM centos:7

# Labels
LABEL io.slateci.image.name="basic-auth"
LABEL io.slateci.image.tags=""
LABEL org.opencontainers.image.authors=""
LABEL org.opencontainers.image.description="This is generalized container meant to support basic Authentication and SSH through SSSD integration to AD/Kerberos/LDAP."
LABEL org.opencontainers.image.licenses="Unlicense"
LABEL org.opencontainers.image.title="Basic Auth"
LABEL org.opencontainers.image.url="https://github.com/slateci/docker-images"
LABEL org.opencontainers.image.vendor="SLATECI"
LABEL org.opencontainers.image.version="1.0.18"

RUN yum update -y && \
    yum install -y epel-release && \
    yum install -y sssd authconfig openssh-server supervisor && \
    yum clean all

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY startup.sh /etc/startup.sh

# --enablesssd sets up nssswitch.conf with sssd
# --enablesssdauth sets up pam with sssd
RUN authconfig --update --enablesssd --enablesssdauth --enablemkhomedir

RUN chmod +x /etc/startup.sh

CMD ["/bin/sh", "-c", "/etc/startup.sh && /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf"]