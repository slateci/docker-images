FROM centos:7

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
