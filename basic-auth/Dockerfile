FROM centos:7

# Security updates necessary as of 2021/04/28
RUN yum install -y --security --bugfix python && \
    yum install -y --security --bugfix glibc && \
    yum install -y --security --bugfix curl && \
    yum install -y --security --bugfix libldb

RUN yum install -y epel-release && \
    yum install -y openssh-server supervisor sssd authconfig && \
    yum clean all

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY startup.sh /etc/startup.sh

RUN chmod +x /etc/startup.sh

# --enablesssd sets up nssswitch.conf with sssd
# --enablesssdauth sets up pam with sssd
RUN authconfig --update --enablesssd --enablesssdauth --enablemkhomedir


CMD ["/bin/sh", "-c", "/etc/startup.sh && /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf"]
