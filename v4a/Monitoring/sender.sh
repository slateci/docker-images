#!/bin/sh


if [ -n $MONITOR_ES ]
then
  if [ $MONITOR_ES != "true" ]
  then
    echo "NO MONITOR OK"
    exit 0
  fi
else
  echo -e "MONITOR_ES not set.\n"
  exit 0
fi

data=$(varnishstat -j)

jsn=$(echo $data | jq --arg INST "$INSTANCE" --arg SITE "$SITE" '. += { instance: $INST, site: $SITE }')

timeout 2 curl --request POST -L -k \
  --url http://varnish.atlas-ml.org:80/ \
  --header 'content-type: application/json' \
  --data "$jsn"

exit 0