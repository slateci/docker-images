FROM perfsonar/testpoint:v4.3.4
LABEL maintainer="SLATE Team"

COPY run-perfsonar-tests.sh /usr/local/bin/run-perfsonar-tests.sh
COPY supervisord.conf /etc/supervisord.conf
CMD /usr/bin/supervisord -c /etc/supervisord.conf
