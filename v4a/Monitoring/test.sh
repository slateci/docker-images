apt-get install snmpd snmp libsnmp-dev -y

/etc/init.d/snmpd stop 
/usr/sbin/snmpd -LS 5 d -Lf /var/log/snmpd.log -p /var/run/snmpd.PID -a -d -V
tail -f /var/log/snmpd.log
 
snmpwalk  -v2c -Cc -c public localhost:3401 .1.3.6.1.4.1.3495.1.1.1.0
snmpwalk  -v2c -Cc -c public localhost:3401 .1.3.6.1.4.1.3495.1.3.1.7.0
snmpwalk  -v2c -Cc -c public localhost:3401 .1.3.6.1.4.1.3495.1.1
snmpwalk  -v2c -Cc -c public localhost:3401 .1.3.6.1.4.1.3495
