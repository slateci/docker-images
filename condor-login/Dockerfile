FROM opensciencegrid/osg-wn
LABEL maintainer="Lincoln Bryant <lincolnb@uchicago.edu>"

# hadolint ignore=DL3031
RUN yum update -y
 
#RUN yum install -y epel-release

RUN yum install -y openssh-server pwgen supervisor authconfig
  
RUN yum install openssl -y

# from Mats
#RUN curl -s -o /etc/yum.repos.d/htcondor-testing-rhel7.repo https://research.cs.wisc.edu/htcondor/yum/repo.d/htcondor-testing-rhel7.repo \
# && echo "priority=10" >>/etc/yum.repos.d/htcondor-testing-rhel7.repo \
# && rpm --import http://research.cs.wisc.edu/htcondor/yum/RPM-GPG-KEY-HTCondor \
# && yum -y install condor \
# && mkdir -p /etc/condor/passwords.d /etc/condor/tokens.d \
# && yum clean all
RUN yum install -y condor

RUN yum -y install osg-flock

# ran into a weird problem here

# Copy the Gratia probe into the correct place - FIXME
#RUN cp /etc/gratia/condor/ProbeConfig-flocking /etc/gratia/condor/ProbeConfig

# not sure what this does. can we remove it?
RUN echo > /etc/sysconfig/i18n

# Clean up after yum:
RUN yum clean all && rm -rf /var/cache/yum

COPY container-files /

RUN yum install -y openssh-clients \ 
  libXt \
  tcsh \
  gcc \
  libXpm \
  libXpm-devel \
  unzip
#  yum install http://linuxsoft.cern.ch/wlcg/centos7/x86_64/wlcg-repo-1.0.0-1.el7.noarch.rpm -y && \
#  yum install HEP_OSlibs -y && \
RUN yum clean all

# not needed for now
#RUN mkdir -p /var/lib/condor/credentials

# Preemptive FIXME
#RUN sed -i 's/EnableProbe="0"/EnableProbe="1"/' /etc/gratia/condor/ProbeConfig

COPY 10-base.conf /etc/condor/config.d/

COPY fetch-crl /etc/cron.d/

ENTRYPOINT ["/config/bootstrap.sh"]
