FROM centos:7
LABEL maintainer="Lincoln Bryant <lincolnb@uchicago.edu>"

# hadolint ignore=DL3031
RUN yum update -y && yum install -y epel-release

RUN curl -LOs https://downloads.globus.org/toolkit/globus-connect-server/globus-connect-server-repo-latest.noarch.rpm
RUN rpm --import https://downloads.globus.org/toolkit/gt6/stable/repo/rpm/RPM-GPG-KEY-Globus
RUN yum install globus-connect-server-repo-latest.noarch.rpm -y

RUN yum install yum-plugin-priorities -y
RUN yum install globus-connect-server supervisor -y

# Clean up after yum:
RUN yum clean all && rm -rf /var/cache/yum

COPY supervisord.conf /etc/supervisord.conf
COPY supervisord_startup.sh /usr/local/bin/supervisord_startup.sh
RUN chmod +x /usr/local/bin/supervisord_startup.sh

ENTRYPOINT ["/usr/local/bin/supervisord_startup.sh"]
