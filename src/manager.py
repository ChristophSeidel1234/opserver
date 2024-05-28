#!/bin/python
from dataclasses import dataclass
import yaml
import json
import os
from typing import Any, List
from requests import get
import re
from faillog import QSLog
from analyze import IstioDAnalyze
from clusters import Cluster


@dataclass
class WorkloadSelector():
    namespace: str
    key: str
    value: str
    wtype: str = "pod"

    def __post_init__(self):
        if self.wtype not in ["pod", "service"]:
            raise ValueError(f"{self.wtype} not a valid Workloadtype. Allowed values are ['pod', 'service'].")

class ResourceLimits():
    def __init__(self):
        if os.path.exists("/config/limits.yaml"):
            with open("/config/limits.yaml", "r") as f:
                self.__limits:dict = yaml.safe_load(f)
        else:
            print("No Limit Config set. Using default....")
            self.__limits = {
                "istio-ingressgateway": {
                    "cpu": "6", "memory": "24Gi"
                },
                "kube-prometheus-stack-prometheus": {
                    "cpu": "2", "memory": "50000Mi"
                },
                "prometheus": {
                    "cpu": "2", "memory": "50000Mi"
                },
                "rancher-monitoring-prometheus": {
                    "cpu": "2", "memory": "50000Mi"
                }
            }
        print(self.__limits)
        self.__limits = json.loads(json.dumps(self.__limits), parse_int=str, parse_float=str)
    
    def get(self, ressource:str):
        return self.__limits.get(ressource, None)
    

class Manager():
    '''Manager QS Functions
    
    Attributes
    ----------
    url: str
        the cluster rancher URL
    token : str
        Bearer Authentification token
    log : QSLog
        Logging Descriptor
    debug: bool, default: False
        debug mechanism
    '''
    
    def __init__(self, url: str, token: str, log: QSLog, limits:ResourceLimits,  debug_:bool=False, verify:bool=False) -> None:
        self.__url = url
        self.__limits = limits
        self.__token = token
        self.__debug = debug_
        self.__verify = verify
        self.__log = log


    def __getk8s(self, url:str) -> Any:
        base = self.__url.replace("v3", "k8s")
        url = f"{base}{url}"
        if self.__debug:
            print(f"GET {url}")
        response = get(url=url, headers={"Authorization": "Bearer {}".format(self.__token)}, verify=self.__verify) #self.__debug
        try:
            data = response.json()
            if "items" in data.keys():
                return data["items"]
            if "kind" in data.keys():
                return data
        except:
            logs = response.text.split("\n")
            if len(logs)>10:
                return logs
            return None

    def __get(self, url:str) -> Any:
        '''
        Get Raw URLs

        Params
        ------
        url : str
            the URL to get.

        Returns
        -------
        None or dict. Depending on return values
        '''
        url = f"{self.__url}{url}"
        try:
            response = get(url=url, headers={"Authorization": "Bearer {}".format(self.__token)}, verify=self.__verify) # self.__debug
            if response.status_code == 200:
                data = response.json()
                if "data" in data.keys():
                    return data["data"]
                return data
            return None
        except Exception as e:
            print(e)
            return None

    def runNodeQS(self, cluster: Cluster) -> None:
        nodes = self.__get(f"/clusters/{cluster.id}/nodes")
        if not nodes:
            self.__log.write(f"[\033[0;31mFailed\033[0m]\tCluster {cluster.name} not reachable...")
        else:
            fails = []
            for node in nodes:
                conditionMet = self.__metNodeConditions(node["conditions"])
                # if this is None -> conditons are met
                if conditionMet:
                    fails.append((node["nodeName"], conditionMet))
            if fails:
                self.__log.write(f"[\033[0;31mFailed\033[0m]\tCluster {cluster.name} failed with nodes: {fails}")
            else:
                self.__log.write(f"[ \033[0;32mOK\033[0m ]\t\tCluster {cluster.name} passed Node inspection.")

    def runPrometheusInspection(self, cluster: Cluster, nsSystemId: str) -> None:
        '''
        Check Prometheus and check scaling of Nodes
        
        Params
        ------
        cluster : dict
            cluster information
        nsSystemId: str
            the ID of Rancher Project System
        '''
        if not nsSystemId:
            self.__log.write(f"[\033[0;31mFailed\033[0m]\tCluster {cluster.name} not reachable...")
        else:
            #provSet = self.__get(f"/projects/{nsSystemId}/daemonsets?name=prometheus-node-exporter")
            provSet = self.__get(f"/projects/{nsSystemId}/daemonsets?name=rancher-monitoring-prometheus-node-exporter")
            if not provSet:
                self.__log.write(f"[\033[0;31mFailed\033[0m]\tCluster {cluster.name} Prometheus Scaling. Desired: {cluster.n_nodes} | Available: NONE")
                return
            status = provSet[0]["daemonSetStatus"]
            if len({status['currentNumberScheduled'], status['desiredNumberScheduled'], status['numberAvailable'], cluster.n_nodes}) == 1:
                self.__log.write(f"[ \033[0;32mOK\033[0m ]\t\tCluster {cluster.name} passed Prometheus scaling.")
            else:
                self.__log.write(f"[\033[0;31mFailed\033[0m]\tCluster {cluster.name} Prometheus Scaling. Desired: {cluster.n_nodes} | Available: {status['numberAvailable']}")

    def runIstioCNIInspection(self, cluster: Cluster, nsSystemId: str):
        '''
        Check istio CNI and check scaling of Nodes
        
        Params
        ------
        cluster : dict
            cluster information
        nsSystemId: str
            the ID of Rancher Project System
        '''
        if not nsSystemId:
            self.__log.write(f"[\033[0;31mFailed\033[0m]\tCluster {cluster.name} not reachable...")
        else:
            provSet = self.__get(f"/projects/{nsSystemId}/daemonsets?name=istio-cni-node")
            if not provSet:
                self.__log.write(f"[\033[0;31mFailed\033[0m]\tCluster {cluster.name} Istio CNI Scaling. Desired: {cluster.n_nodes} | Available: NONE")
                return
            status = provSet[0]["daemonSetStatus"]
            if len({status['currentNumberScheduled'], status['desiredNumberScheduled'], status['numberAvailable'], cluster.n_nodes}) == 1:
                self.__log.write(f"[ \033[0;32mOK\033[0m ]\t\tCluster {cluster.name} passed Istio CNI scaling.")
            else:
                self.__log.write(f"[\033[0;31mFailed\033[0m]\tCluster {cluster.name} Istio CNI Scaling. Desired: {cluster.n_nodes} | Available: {status['numberAvailable']}")

    def runCanalInspection(self, cluster: Cluster, nsSystemId: str) -> None:
        '''
        Check Canal and check scaling of Nodes
        
        Params
        ------
        cluster : dict
            cluster information
        nsSystemId: str
            the ID of Rancher Project System
        '''
        if not nsSystemId:
            self.__log.write(f"[\033[0;31mFailed\033[0m]\tCluster {cluster.name} not reachable...")
        else:
            provSet = self.__get(f"/projects/{nsSystemId}/daemonsets?name=canal")
            if not provSet:
                self.__log.write(f"[\033[0;31mFailed\033[0m]\tCluster {cluster.name} Canal Scaling. Desired: {cluster.n_nodes} | Available: NONE")
                return
            status = provSet[0]["daemonSetStatus"]
            if len({status['currentNumberScheduled'], status['desiredNumberScheduled'], status['numberAvailable'], cluster.n_nodes}) == 1:
                self.__log.write(f"[ \033[0;32mOK\033[0m ]\t\tCluster {cluster.name} passed Canal scaling.")
            else:
                self.__log.write(f"[\033[0;31mFailed\033[0m]\tCluster {cluster.name} Canal Scaling. Desired: {cluster.n_nodes} | Available: {status['numberAvailable']}")

    def checkPrometheus(self, cluster:Cluster, nsSystemId: str) -> None:
        '''
        Check Prometheus deployments. If there is any deployment not "active"
        
        Params
        ------
        cluster : dict
            cluster information
        nsSystemId: str
            the ID of Rancher Project System
        '''
        if not nsSystemId:
            self.__log.write(f"[\033[0;31mFailed\033[0m]\tCluster {cluster.name} not reachable...")
        else:
            provSet = self.__get(f"/projects/{nsSystemId}/workloads?namespaceId=cattle-monitoring-system")
            if not provSet:
                self.__log.write(f"[\033[0;31mFailed\033[0m]\tCluster {cluster.name} has failed Prometheus deployments. No Deployments with active status.")
                return
            if any(deployment["state"] != 'active' for deployment in provSet):
                fails = [deployment["name"] for deployment in provSet if deployment["state"] != 'active']
                self.__log.write(f"[\033[0;31mFailed\033[0m]\tCluster {cluster.name} has failed Prometheus deployments: {fails}")
            else:
                self.__log.write(f"[ \033[0;32mOK\033[0m ]\t\tCluster {cluster.name} has all Prometheus deployments.")
            
    def checkMonitoring(self, cluster:Cluster, nsMonitoringId: str) -> None:
        '''
        Not implemented yet....
        '''
        pass

    def istioDlogs(self, cluster:Cluster, nsSystemId:str) -> None:
        '''
        '''
        def dataInject(data: dict, inject: dict) -> dict:
            return dict(data, **inject)
        def getIstioVersion(pods: list) -> dict:
            versions = dict()
            for pod in pods:
                label = pod["metadata"]["labels"].get("istio.io/rev")
                image_tag = pod["spec"]["containers"][0]["image"].split(":")[-1]
                if label not in versions:
                    versions[label] = {"count": 1, "image_tag": [image_tag]} 
                else:
                    versions[label]["count"] += 1
                    if image_tag not in versions[label]["image_tag"]:
                        versions[label]["image_tag"].append(image_tag) 
            return versions

        if not nsSystemId:
            self.__log.write(f"[\033[0;31mFailed\033[0m]\tCluster {cluster.name} not reachable...")
        else:
            splashes = []
            pods = self.__getk8s(f"/clusters/{nsSystemId.split(':')[0]}/api/v1/namespaces/istio-system/pods?labelSelector=app=istiod")
            # allows checking of istiod deployments :)
            # min pods == 1
            print("Anzahl der Pods: ", len(pods))
            if len(pods) < 1:
                self.__log.write(f"[\033[0;31mFailed\033[0m]\tCluster {cluster.name} deployed too few istiod pods")
            else:
                for k,v in getIstioVersion(pods).items():
                    self.__log.write(f"[ \033[0;32mOK\033[0m ]\t\tCluster {cluster.name} deployed {v['count']} {k}-istiod pods with image_tags {v['image_tag']}")
            for pod in pods:
                podID = pod["metadata"]["name"]
                logs = self.__getk8s(f"/clusters/{nsSystemId.split(':')[0]}/api/v1/namespaces/istio-system/pods/{podID}/log?sinceSeconds=70")
                if logs:
                    logsplash = IstioDAnalyze(logs=logs).analyze()
                    if len(logsplash) > 0:
                        splashes.extend(logsplash)
            if splashes:
                splashes = [
                    dataInject(splash, {
                        "cluster": cluster.name,
                        "id": cluster.id
                    }) for splash in splashes
                ]
                istioSplash = list(set([splash['trace'] for splash in splashes]))
                self.__log.write(f"[ \033[1;33mWARN\033[0m ]\tCluster {cluster.name} has failed istiod logs {istioSplash}")
            else:
                self.__log.write(f"[ \033[0;32mOK\033[0m ]\t\tCluster {cluster.name} passed istiod-logs.")

    def checkRessources(self, cluster: Cluster, nsSystemId: str, selector: WorkloadSelector):
        def compareResource(limit, value):
            def compareRAM(a,b):
                a = re.match(r'([\d]*)([\w]*)', a).groups()
                b = re.match(r'([\d]*)([\w]*)', b).groups()
                if a[1]==b[1]:
                    if int(a[0])>int(b[0]):
                        return False
                elif a[1]>b[1]:
                    if int(a[0])>int(b[0])*1024:
                        return False
                else:
                    if int(a[0])*1024>int(b[0]):
                        return False
                return True
            diffCPU=limit["cpu"]<=value["cpu"]
            diffRAM=compareRAM(limit["memory"],value["memory"])
            return diffCPU&diffRAM, {"cpu": diffCPU, "memory": diffRAM, "input": (limit,value)}
        if not all([nsSystemId, selector]):
            self.__log.write(f"[\033[0;31mFailed\033[0m]\tCluster {cluster.name} not reachable...")
        else:
            workloads = self.__getk8s(f"/clusters/{nsSystemId.split(':')[0]}/api/v1/namespaces/{selector.namespace}/pods?labelSelector={selector.key}={selector.value}")
            if len(workloads)==0:
                # no workload found...
                self.__log.write(f"[\033[0;31mFailed\033[0m]\tCluster {cluster.name} has no Ressources with {selector.key}:{selector.value} in Namespace: {selector.namespace}")
                return
            diffs = []
            for workload in workloads:
                ID = workload["metadata"]["name"]
                data = self.__getk8s(f"/clusters/{nsSystemId.split(':')[0]}/api/v1/namespaces/{selector.namespace}/pods/{ID}")
                # get first container
                container = data["spec"]["containers"][0]
                diff = compareResource(self.__limits.get(selector.value), container["resources"]["limits"])
                diffs.append(diff)
            if not all(d[0] for d in diffs):
                for diff in diffs:
                    if not diff[0]:
                        self.__log.write(f"[\033[0;31mFailed\033[0m]\tCluster {cluster.name} has failed RessourceCheck {selector.value} with {diff[1]}")
            else:
                self.__log.write(f"[ \033[0;32mOK\033[0m ]\t\tCluster {cluster.name} passed RessourceCheck {selector.value}.")

    def checkVolumes(self, cluster: Cluster, nsSystemId: str, selector: WorkloadSelector) -> None:
        if not all([nsSystemId, selector]):
            self.__log.write(f"[\033[0;31mFailed\033[0m]\tCluster {cluster.name} not reachable...")
        else:
            workloads = self.__getk8s(f"/clusters/{nsSystemId.split(':')[0]}/api/v1/namespaces/{selector.namespace}/pods?labelSelector={selector.key}={selector.value}")
            for workload in workloads:
                ID = workload["metadata"]["name"]
                data = self.__getk8s(f"/clusters/{nsSystemId.split(':')[0]}/api/v1/namespaces/{selector.namespace}/pods/{ID}")
                volumes = data["spec"]["volumes"]
                pvs = [v["persistentVolumeClaim"]["claimName"] for v in volumes if "persistentVolumeClaim" in v.keys()]

    def checkLifeTime(self, cluster: dict, nsSystemId:str) -> None:
        '''
        '''
        pass


    def __metNodeConditions(self, nodeConditions: list) -> dict[str, Any]:
        '''
        Tests the nodes conditions against a predefined pattern
    
        Parameters
        ----------
        nodeConditions: dict
            conditions from each node  in a cluster
    
        Returns
        -------
        None if conditions are Met. Not met conditions otherwise
        
        '''
        test = {'Initialized': 'True', 'Registered': 'True', 'Provisioned': 'True', 'NetworkUnavailable': 'False', 'MemoryPressure': 'False', 'DiskPressure': 'False', 'PIDPressure': 'False', 'Ready': 'True'}
        ret =  {k:cond["status"] for k,t in test.items() for cond in nodeConditions if (cond["type"]==k and cond["status"]!=t)}
        return ret
    
    def runQS(self, clusters:List[Cluster]):
        '''
        Main handler for QS Runtime
        
        Params
        ------
        clusters : List[dict]
            list of clusters to scrape from
        '''
        for cluster in clusters:
            print("--------\n[ \033[1;35mChecking\033[0m ] {}".format(cluster.name))
            #nsSystemId = self.__get(f"/clusters/{cluster.id}/projects?name=System")
            nsSystemId = self.__get(f"/clusters/{cluster.id}/projects?name=System")
            nsSystemId = nsSystemId[0]["id"]
            self.runNodeQS(cluster=cluster)
            self.runPrometheusInspection(cluster=cluster, nsSystemId=nsSystemId)
            self.runCanalInspection(cluster=cluster, nsSystemId=nsSystemId)
            self.checkPrometheus(cluster=cluster, nsSystemId=nsSystemId)
            self.runIstioCNIInspection(cluster=cluster, nsSystemId=nsSystemId)
            self.istioDlogs(cluster=cluster, nsSystemId=nsSystemId)
            self.checkRessources(cluster, nsSystemId=nsSystemId, selector=WorkloadSelector(namespace="istio-system", key="app", value="istio-ingressgateway"))
            self.checkRessources(cluster, nsSystemId=nsSystemId, selector=WorkloadSelector(namespace="cattle-monitoring-system", key="prometheus", value="rancher-monitoring-prometheus"))

    