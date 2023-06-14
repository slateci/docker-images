echo "Starting Varnish on port $VARNISH_PORT"
echo "Using $VARNISH_MEM memory, and $VARNISH_TRANSIENT_MEM"

if [ -n $MONITOR_SNMP ]
then
  if [ $MONITOR_SNMP = "true" ]
  then
    # service snmpd start
    # /usr/sbin/snmpd -LS 5 d -Lf /var/log/snmpd.log -p /var/run/snmpd.PID -a -d -V
    /usr/sbin/snmpd -LS 5 d -Lf /var/log/snmpd.log -p /var/run/snmpd.PID -a -d
    
  fi
fi

chsh -s /bin/bash varnish
su varnish -c '/usr/sbin/varnishd -F -f /etc/varnish/default.vcl -a http=:$VARNISH_PORT,HTTP -a proxy=:8443,PROXY -p feature=+http2 -p max_restarts=8 -s malloc,$VARNISH_MEM -s Transient=malloc,$VARNISH_TRANSIENT_MEM'