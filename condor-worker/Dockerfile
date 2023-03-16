#FROM opensciencegrid/osg-wn:3.5-el7
FROM htcondor/execute:lts-el8

# Labels
LABEL io.slateci.image.name="condor-worker"
LABEL io.slateci.image.tags=""
LABEL org.opencontainers.image.authors="lincolnb@uchicago.edu"
LABEL org.opencontainers.image.description=""
LABEL org.opencontainers.image.licenses="Unlicense"
LABEL org.opencontainers.image.title="Condor Worker"
LABEL org.opencontainers.image.url="https://github.com/slateci/docker-images"
LABEL org.opencontainers.image.vendor="SLATECI"
LABEL org.opencontainers.image.version="10.0.2"

# another hack- we need to remove singularity and replace it with Igor's script
# that wraps around the singularity binary from CVMFS and removes the --pid
# option
#No longer part of the base image hence should eventually be removed - MA 20230313
#RUN yum remove -y singularity

# libXt needed for some application
# tcsh needed for fsurf
# ATLAS needs unzip, gcc at least.
RUN yum -y install openssh-clients \
                   openssh-server \
                   libXt \
                   tcsh \
                   gcc \
                   libXpm \
                   libXpm-devel \
                   supervisor \
                   unzip && \
    yum install https://linuxsoft.cern.ch/wlcg/centos8/x86_64/wlcg-repo-1.0.0-1.el8.noarch.rpm -y && \
    yum install HEP_OSlibs -y && \
    yum clean all

COPY container-files /
RUN mkdir -p /var/lib/condor/credentials

RUN curl -Ls https://raw.githubusercontent.com/opensciencegrid/osg-flock/master/node-check/osgvo-node-advertise \
    -o /usr/local/bin/osgvo-node-advertise && \
    chmod +x /usr/local/bin/osgvo-node-advertise
RUN curl -Ls https://raw.githubusercontent.com/opensciencegrid/osg-flock/master/job-wrappers/user-job-wrapper.sh \
    -o /usr/libexec/condor/user-job-wrapper.sh && \
    chmod +x /usr/libexec/condor/user-job-wrapper.sh

### Temporary hack for making the glidein scripts work
RUN chmod 777 /var/log/condor

# GPU stuff, sort this out later!
#RUN yum localinstall http://developer.download.nvidia.com/compute/cuda/repos/rhel7/x86_64/cuda-repo-rhel7-9.2.148-1.x86_64.rpm -y
#RUN yum install cuda-drivers-390.12 xorg-x11-drv-nvidia-390.12 xorg-x11-drv-nvidia-devel-390.12 xorg-x11-drv-nvidia-gl-390.12 xorg-x11-drv-nvidia-libs-390.12 nvidia-kmod-390.12  -y
#RUN yum install cuda-9.1.85 -y
#RUN ln -s /usr/local/cuda-9.0 /usr/local/cuda
#RUN curl -OL http://us.download.nvidia.com/XFree86/Linux-x86_64/396.51/NVIDIA-Linux-x86_64-396.51.run
#RUN chmod +x NVIDIA-Linux-x86_64-396.51.run; ./NVIDIA-Linux-x86_64-396.51.run -s

# We may mount /var/lib/docker from the host, so we chown that
ENTRYPOINT /etc/osg/image-config.d/fix-perms.sh && \
           chown -R condor: /var/lib/condor && \
           /usr/bin/supervisord -c /etc/supervisord.conf
