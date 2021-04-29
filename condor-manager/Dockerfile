FROM opensciencegrid/software-base:fresh

RUN yum update -y && yum install -y epel-release

# upcoming for tokens
RUN yum install -y --enablerepo=osg-upcoming --enablerepo=osg-empty \
  condor \
  pwgen \
  supervisor \
  openssl \
  gratia-probe-glideinwms \
  gratia-probe-common \
  gratia-probe-condor \
  python2-scitokens-credmon \
  empty-ca-certs \
  glibc-static \
  wget \
  curl

RUN yum clean all && rm -rf /tmp/yum*

ADD container-files /

CMD ["/usr/local/sbin/supervisord_startup.sh"]