#!/usr/bin/env python3
import subprocess
import os
import sys


def to_kB(vars):
    inp = vars[0]
    return int(int(inp)/1024)


def to_MB(vars):
    inp = vars[0]
    return int(int(inp)/1048576)


def get_instance(vars):
    return os.getenv("SITE", default="TestSite")+"_"+os.getenv("INSTANCE", default="Inst-01")


class VarnishStatus:

    def get_beresp_kb(self, vars):
        res = 0
        for k in self.v_metrics.keys():
            if k.startswith('VBE.boot.') and k.count('beresp'):
                res += int(self.v_metrics[k])
        return res/1024

    def __init__(self, oid_prefix):

        i = 'integer'
        s = 'string'
        c = 'counter'
        g = 'gauge'
        t = 'timeticks'
        o = 'octet'

        self.sq_oids = {
            '1.1.1': [i, 9, 'cacheSysVMsize',  to_kB, "SMA.s0.c_bytes"],
            '1.1.2': [i, 0, 'cacheSysStorage'],  # Storage Swap size in KB
            '1.1.3': [t, 9, 'cacheUptime', "MAIN.uptime"],
            '1.2.1': [s, 'ivukotic@uchicago.edu', 'cacheAdmin'],
            '1.2.2': [s, 'varnish', 'cacheSoftware'],  # Cache Software Name
            '1.2.3': [s, '7.1', 'cacheVersionId'],  # Cache Software Version
            '1.2.4': [s, 'ALL,1', 'cacheLoggingFacility'],  # Logging Facility.
            '1.2.5.1': [i, 9, 'cacheMemMaxSize', to_MB, "SMA.s0.g_space"],
            '1.2.5.2': [i, 0, 'cacheSwapMaxSize'],
            '1.2.5.3': [i, 0, 'cacheSwapHighWM'],
            '1.2.5.4': [i, 0, 'cacheSwapLowWM'],
            '1.2.6': [s, 'varnish-test', 'cacheUniqName', get_instance],
            '1.3.1.1': [c, 0, 'cacheSysPageFaults'],  # ?
            '1.3.1.2': [c, 0, 'cacheSysNumReads'],  # ?
            '1.3.1.3': [i, 9, 'cacheMemUsage',  to_MB, "SMA.s0.c_bytes"],
            '1.3.1.4': [i, 0, 'cacheCpuTime'],  # TODO accumulative CPU seconds
            '1.3.1.5': [i, 0, 'cacheCpuUsage'],  # TODO percent usage
            '1.3.1.6': [i, 0, 'cacheMaxResSize'],  # ?
            '1.3.1.7': [g, 0, 'cacheNumObjCount', 'MAIN.n_object'],
            '1.3.1.8': [t, 0, 'cacheCurrentLRUExpiration'],
            '1.3.1.9': [g, 0, 'cacheCurrentUnlinkRequests'],
            '1.3.1.10': [g, 0, 'cacheCurrentUnusedFDescrCnt'],
            '1.3.1.11': [g, 0, 'cacheCurrentResFileDescrCnt'],
            '1.3.1.12': [g, 0, 'cacheCurrentFileDescrCnt'],
            '1.3.1.13': [g, 0, 'cacheCurrentFileDescrMax'],
            '1.3.2.1.1': [c, 0, 'cacheProtoClientHttpRequests', "MAIN.client_req"],
            '1.3.2.1.2': [c, 0, 'cacheHttpHits', "MAIN.cache_hit"],
            '1.3.2.1.3': [c, 0, 'cacheHttpErrors'],  # ?
            '1.3.2.1.4': [c, 0, 'cacheHttpInKb', self.get_beresp_kb],
            '1.3.2.1.5': [c, 0, 'cacheHttpOutKb', to_kB, "MAIN.s_resp_bodybytes"],
            '1.3.2.1.6': [c, 0, 'cacheIcpPktsSent'],
            '1.3.2.1.7': [c, 0, 'cacheIcpPktsRecv'],
            '1.3.2.1.8': [c, 0, 'cacheIcpKbSent'],
            '1.3.2.1.9': [c, 0, 'cacheIcpKbRecv'],
            '1.3.2.1.10': [i, 'cacheServerRequests', "MAIN.cache_hit"],
            '1.3.2.1.11': [i, 0, 'cacheServerErrors'],
            '1.3.2.1.12': [c, 0, 'cacheServerInKb', self.get_beresp_kb],  # ?
            '1.3.2.1.13': [c, 0, 'cacheServerOutKb'],  # ?
            '1.3.2.1.14': [g, 0, 'cacheCurrentSwapSize'],
            '1.3.2.1.15': [g, 0, 'cacheClients'],  # ?
            "1.3.2.2.1.1.1": [i, 1,  "cacheMedianTime.1"],  # ?
            "1.3.2.2.1.1.5": [i, 5,  "cacheMedianTime.5"],  # ?
            "1.3.2.2.1.1.60": [i, 60, "cacheMedianTime.60"],  # ?
            "1.3.2.2.1.2.1": [i, 0,  "cacheHttpAllSvcTime.1"],
            "1.3.2.2.1.2.5": [i, 0,  "cacheHttpAllSvcTime.5"],
            "1.3.2.2.1.2.60": [i, 0, "cacheHttpAllSvcTime.60"],
            "1.3.2.2.1.3.1": [i, 0,  "cacheHttpMissSvcTime.1"],  # TODO
            "1.3.2.2.1.3.5": [i, 0,  "cacheHttpMissSvcTime.5"],  # TODO
            "1.3.2.2.1.3.60": [i, 0, "cacheHttpMissSvcTime.60"],  # TODO
            "1.3.2.2.1.4.1": [i, 0,  "cacheHttpNmSvcTime.1"],
            "1.3.2.2.1.4.5": [i, 0,  "cacheHttpNmSvcTime.5"],
            "1.3.2.2.1.4.60": [i, 0, "cacheHttpNmSvcTime.60"],
            "1.3.2.2.1.5.1": [i, 0,  "cacheHttpHitSvcTime.1"],
            "1.3.2.2.1.5.5": [i, 0,  "cacheHttpHitSvcTime.5"],
            "1.3.2.2.1.5.60": [i, 0, "cacheHttpHitSvcTime.60"],
            "1.3.2.2.1.6.1": [i, 0,  "cacheIcpQuerySvcTime.1"],
            "1.3.2.2.1.6.5": [i, 0,  "cacheIcpQuerySvcTime.5"],
            "1.3.2.2.1.6.60": [i, 0, "cacheIcpQuerySvcTime.60"],
            "1.3.2.2.1.7.1": [i, 0,  "cacheIcpReplySvcTime.1"],
            "1.3.2.2.1.7.5": [i, 0,  "cacheIcpReplySvcTime.5"],
            "1.3.2.2.1.7.60": [i, 0, "cacheIcpReplySvcTime.60"],
            "1.3.2.2.1.8.1": [i, 0,  "cacheDnsSvcTime.1"],
            "1.3.2.2.1.8.5": [i, 0,  "cacheDnsSvcTime.5"],
            "1.3.2.2.1.8.60": [i, 0, "cacheDnsSvcTime.60"],
            "1.3.2.2.1.9.1": [i, 0,  "cacheRequestHitRatio.1"],  # TODO
            "1.3.2.2.1.9.5": [i, 0,  "cacheRequestHitRatio.5"],  # TODO
            "1.3.2.2.1.9.60": [i, 0, "cacheRequestHitRatio.60"],  # TODO
            "1.3.2.2.1.10.1": [i, 0, "cacheRequestByteRatio.1"],  # TODO
            "1.3.2.2.1.10.5": [i, 0, "cacheRequestByteRatio.5"],  # TODO
            "1.3.2.2.1.10.60": [i, 0, "cacheRequestByteRatio.60"],  # TODO
            "1.3.2.2.1.11.1": [i, 0, "cacheHttpNhSvcTime.1"],  # ?
            "1.3.2.2.1.11.5": [i, 0, "cacheHttpNhSvcTime.5"],  # ?
            "1.3.2.2.1.11.60": [i, 0, "cacheHttpNhSvcTime.60"],  # ?
            "1.4.1.1": [g, 0,  "cacheIpEntries"],  # ?
            "1.4.1.2": [c, 0,  "cacheIpRequests"],  # ?
            "1.4.1.3": [c, 0,  "cacheIpHits"],  # ?
            "1.4.1.4": [g, 0,  "cacheIpPendingHits"],
            "1.4.1.5": [c, 0,  "cacheIpNegativeHits"],
            "1.4.1.6": [c, 0,  "cacheIpMisses"],  # ?
            "1.4.1.7": [c, 0,  "cacheBlockingGetHostByName"],
            "1.4.1.8": [c, 0,  "cacheAttemptReleaseLckEntrries"],
            "1.4.2.1": [g, 0,  "cacheFqdnEntries"],  # ?
            "1.4.2.2": [c, 0,  "cacheFqdnRequests"],
            "1.4.2.3": [c, 0,  "cacheFqdnHits"],
            "1.4.2.4": [g, 0,  "cacheFqdnPendingHits"],
            "1.4.2.5": [c, 0,  "cacheFqdnNegativeHits"],
            "1.4.2.6": [c, 0,  "cacheFqdnMisses"],
            "1.4.2.7": [c, 0,  "cacheBlockingGetHostByAddr"],
            "1.4.3.1": [c, 0,  "cacheDnsRequests"],  # ?
            "1.4.3.2": [c, 0,  "cacheDnsReplies"],  # ?
            "1.4.3.3": [c, 0,  "cacheDnsNumberServers"]  # ?
        }

        self.oid_prefix = oid_prefix
        self.sorted_oids = []
        self.cache_service_status()

        for i in self.sorted_oids:
            print(i)

    def get_oid(self, oid):
        for l in self.sorted_oids:
            if l[0] == oid:
                return l

    def cache_service_status(self):

        # Temporary data structure used to create sorted oid list later
        self.sorted_oids = []

        lines = subprocess.check_output(["/usr/bin/varnishstat -1"],
                                        shell=True).decode("UTF-8").strip().split("\n")

        # print('metrics loaded:', len(lines))
        self.v_metrics = {}
        for line in lines:
            [v_name, v_val] = line.split()[: 2]
            self.v_metrics[v_name] = v_val

        for o, v in self.sq_oids.items():
            fo = self.oid_prefix+'.'+o
            if len(v) == 3:  # fixed value
                self.sorted_oids.append([fo, v[0], v[1]])
                continue
            if isinstance(v[3], str):  # simple replacement
                self.sorted_oids.append([fo, v[0], self.v_metrics[v[3]]])
                continue
            args = []
            for c in v[4:]:
                args.append(self.v_metrics[c])
            self.sorted_oids.append([fo, v[0], v[3](args)])


def main():
    oid_prefix = "1.3.6.1.4.1.3495"
    s = VarnishStatus(oid_prefix)

    for ex in s.sorted_oids:
        ex_k = ex[0]
        ex_v = ex[1:]
        if ex_k.startswith(oid_prefix):
            print("." + str(ex_k))
            print(ex_v[0])
            print(str(ex_v[1]))


if __name__ == "__main__":
    main()
