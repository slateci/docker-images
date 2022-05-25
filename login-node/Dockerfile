FROM centos:7

# hadolint ignore=DL3031
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
