# v4A

Varnish for ATLAS

[![DockerPush](https://github.com/ivukotic/v4A/actions/workflows/DockerPush.yml/badge.svg?branch=main)](https://github.com/ivukotic/v4A/actions/workflows/DockerPush.yml)

to test it do:

```sh
setupATLAS
asetup 20.20.6.3,here
export FRONTIER_SERVER=(serverurl=http://v4a.atlas-ml.org:6081/atlr)
db-fnget
```

## TO DO

* check how do we handle TTL
* check memory limits
