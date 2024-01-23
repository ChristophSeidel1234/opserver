#!/bin/python

from json.decoder import JSONDecodeError
from typing import Any, List
from clusters import Cluster
from requests import get
from faillog import QSLog


class Dashboard():
    def __init__(self, url: str, token: str, log: QSLog, proxy:bool=False, debug_:bool=False, verify:bool=False) -> None:
        self.__url = url.replace("/v3","/")
        self.__token = token
        self.__log = log
        self.proxy=proxy
        self.__debug = debug_
        self.__verify = verify

    def get_RAW(self, url:str, params:dict={}, auth:bool=True) -> list[str,Any]:
        '''
        Sends a RAW request to the supplied url and takes optional params

        Params
        ------
        url : str
            the url to request
        params : dict, default: {}
            additional paramters for searching the API

        Returns
        -------
        List[str, Any]
            First Part containing formatted output, second part the Response Status Code or JSON Data. Depending on if there is some JSON Data, or not.
        '''
        try:
            if self.__debug:
                print(f"GET {url} [{auth=}, {params=}]")
            if auth:
                response = get(url=url, headers={"Authorization": "Bearer {}".format(self.__token)}, params=params, verify=self.__verify)
            else:
                response = get(url=url, params=params, verify=self.__verify)
            data = response.json()
            response = response.status_code
        except JSONDecodeError:
            data = None
            response = response.status_code
        except:
            # Failover
            data = None
            response = "ConnectionError"
            return ["[\033[0;31mFailed\033[0m]", response]
        if response == 200:
            return ["[ \033[0;32mOK\033[0m ]\t", data if data else response]
        # extract 500+ as warning -> bad Gateway -> fixable
        elif response%400 > 99:
            return ["[ \033[1;33mWARN\033[0m ]", response]
        else:
            return ["[\033[0;31mFailed\033[0m]", response]

    def get_Prometheus(self, cluster:Cluster) -> None:
        '''
        Scrapes the Prometheus Cluster Endpoint for data.

        Params
        ------
        clusterID : str
            the clusters identifier to scrape from
        clusterName : str
            the clusters name
        '''
        #### prometheus queries...
        cpu_query = '(1 - (avg(irate({__name__=~"node_cpu_seconds_total|windows_cpu_time_total",mode="idle"}[5m])))) * 100'
        memory_query = '(1 - sum({__name__=~"node_memory_MemAvailable_bytes|windows_os_physical_memory_free_bytes"}) / sum({__name__=~"node_memory_MemTotal_bytes|windows_cs_physical_memory_bytes"})) * 100'
        storage_query = '(1 - (((sum(node_filesystem_free_bytes{device!~"rootfs|HarddiskVolume.+"}) OR on() vector(0)) + (sum(windows_logical_disk_free_bytes{volume!~"(HarddiskVolume.+|[A-Z]:.+)"}) OR on() vector(0))) / ((sum(node_filesystem_size_bytes{device!~"rootfs|HarddiskVolume.+"}) OR on() vector(0)) + (sum(windows_logical_disk_size_bytes{volume!~"(HarddiskVolume.+|[A-Z]:.+)"}) OR on() vector(0))))) * 100'
        __path="api/v1/query"
        promURL = {
            'proxy': f'{self.__url}/k8s/clusters/{cluster.id}/api/v1/namespaces/cattle-monitoring-system/services/http:rancher-monitoring-prometheus:9090/proxy/{__path}',
            'standard': f'{cluster.base}/monitoring/prometheus/{__path}'}
        queries = [("cpu", cpu_query), ("memory", memory_query), ("storage", storage_query)]
        output_log = ["[ \033[0;32mOK\033[0m ]\t"]
        used_proxy = ""
        for name, query in queries:
            # try standard url. If Failing. Try Proxy
            url = promURL['standard']
            response = self.get_RAW(url=url, params={"query": query}, auth=False)
            if not isinstance(response[1], dict):
                url = promURL['proxy']
                used_proxy = "[used rancher proxy]"
                response = self.get_RAW(url=url, params={"query": query})
                if not isinstance(response[1], dict):
                    output_log[0] = "[\033[0;31mFailed\033[0m]"
                    output_log.append("xx")
                    continue
            stat = round(float(response[1].get("data").get("result")[0].get("value")[1]),2)
            if stat>65:
                output_log[0] = "[ \033[1;33mWARN\033[0m ]\t\t {} failed QS inspection".format(name)
            output_log.append(stat)
        output_log.insert(1,cluster.name)
        output_log.append(used_proxy)
        self.__log.write("{0}\t{1}: | CPU: {2}% | RAM: {3}% | Storage: {4}% {5}".format(*output_log))

    def __loadPrometheusTargets(self, cluster: Cluster, proxy:bool=False) -> None:
        '''
        Checks Prometheus Targets

        Params
        ------
        clusterID : str
            the clusters identifier to scrape from
        clusterName : str
            the clusters name
        '''
        __path = "targets"
        url = f"{cluster.base}/monitoring/prometheus/{__path}"
        output_log = self.get_RAW(url, auth=False)
        output_log.insert(1,cluster.name)
        self.__log.write("{0}\t{1} : PrometheusTargets returned HTTP | {2}".format(*output_log))
        if proxy:
            url = f"{self.__url}/k8s/clusters/{cluster.id}/api/v1/namespaces/cattle-monitoring-system/services/http:rancher-monitoring-prometheus:9090/proxy/{__path}"
            output_log = self.get_RAW(url)
            output_log.insert(1,cluster.name)
            self.__log.write("{0}\t{1} : PrometheusTargets_proxy returned HTTP | {2}".format(*output_log))
        
    def __loadPrometheusGraph(self, cluster:Cluster, proxy:bool=False) -> None:
        '''
        Checks Prometheus Graphs

        Params
        ------
        clusterID : str
            the clusters identifier to scrape from
        clusterName : str
            the clusters name
        '''
        __path = "graph"
        url = f"{cluster.base}/monitoring/prometheus/{__path}"
        output_log = self.get_RAW(url, auth=False)
        output_log.insert(1,cluster.name)
        self.__log.write("{0}\t{1} : PrometheusGraph returned HTTP | {2}".format(*output_log))
        if proxy:
            url = f"{self.__url}/k8s/clusters/{cluster.id}/api/v1/namespaces/cattle-monitoring-system/services/http:rancher-monitoring-prometheus:9090/proxy/{__path}"
            output_log = self.get_RAW(url)
            output_log.insert(1,cluster.name)
            self.__log.write("{0}\t{1} : PrometheusGraph_proxy returned HTTP | {2}".format(*output_log))

    def __loadJaeger(self, cluster:Cluster) -> None:
        '''
        Checks Jaeger Dashboard

        Params
        ------
        clusterID : str
            the clusters identifier to scrape from
        clusterName : str
            the clusters name
        '''
        url = f"{self.__url}/k8s/clusters/{cluster.id}/api/v1/namespaces/istio-system/services/http:tracing:16686/proxy/jaeger/search"
        output_log = self.get_RAW(url)
        output_log.insert(1,cluster.name)
        self.__log.write("{0}\t{1} : Jaeger returned HTTP | {2}".format(*output_log))

    def load(self, cluster: Cluster, dashboardType: str) -> None:
        '''
        Load Function for each dashboardtype...

        Params
        ------
        cluster : dict
            the clusters identifier and name to scrape from
        dashboardType : str
            dashboardtype as string

        Raises
        ------
        NotImplementedError
            DashboardType not recognized...
        '''
        if dashboardType == "grafana":
            self.get_Prometheus(cluster)
        elif dashboardType == "promTargets":
            self.__loadPrometheusTargets(cluster, self.proxy)
        elif dashboardType == "promGraphs":
            self.__loadPrometheusGraph(cluster, self.proxy)
        elif dashboardType == "jaeger":
            self.__loadJaeger(cluster)
        else:
            raise NotImplementedError()

    def runQS(self, clusters:list[Cluster]) -> None:
        '''
        Main Run function for QS. Does this for each cluster specified. Writes the output data to the QSLog

        Params
        ------
        clusters : List[dict]
            the clusters to scrape data from
        '''
        for cluster in clusters:
            print("--------\n[ \033[1;35mChecking\033[0m ] {}".format(cluster.name))
            if cluster.state == "active":
                self.load(cluster, dashboardType="grafana")
                self.load(cluster, dashboardType="promTargets")
                self.load(cluster, dashboardType="promGraphs")
                self.load(cluster, dashboardType="jaeger") # now on every cluster
            else:
                print("Cluster {} has failed active state...".format(cluster.name))
