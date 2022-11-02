# syntax=docker/dockerfile:1
FROM centos:7

# Labels
LABEL io.slateci.image.name="globus-connect-v4"
LABEL io.slateci.image.tags=""
LABEL org.opencontainers.image.authors="lincolnb@uchicago.edu"
LABEL org.opencontainers.image.description=""
LABEL org.opencontainers.image.licenses="Unlicense"
LABEL org.opencontainers.image.title="Globus Connect - 4"
LABEL org.opencontainers.image.url="https://github.com/slateci/docker-images"
LABEL org.opencontainers.image.vendor="SLATECI"
LABEL org.opencontainers.image.version="4.0.63"

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
