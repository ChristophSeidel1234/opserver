#!/bin/python

from typing import List
from requests import get
from dataclasses import dataclass
import os


@dataclass
class Cluster():
    name:str # Name
    id: str # Rancher ClusterID
    state: str # State
    n_nodes: int # number of Nodes
    environment: List[str] # Description of the cluster location. Can be used afterwards...
    base: str # Ingress Base Domain für Dinge auf dem Cluster

@dataclass
class ClusterConfigCluster():
    name: str
    ingress: str
    environment: List[str] = [""]

@dataclass
class ClusterConfig():
    clusterURL: str
    clusters: List[ClusterConfigCluster]
    apiToken: str = ""
    debug: bool = False
    proxy: bool = True
    verify: bool = True

    def __post_init__(self):
        # check if env-api-token is set
        if os.getenv("API_TOKEN"):
            self.apiToken = os.getenv("API_TOKEN")
        # if not set here or as env -> Throw error
        if self.apiToken == "":
            raise ValueError("No API_TOKEN is set! Please use environment or config.yaml")

@dataclass
class ClusterType():
    name: str
    path:str = None

    def __post_init__(self):
        listTypes = ["rancher", "azure"]
        if self.name in listTypes:
            if self.name == "rancher":
                self.path = "appliedSpec.rancherKubernetesEngineConfig.nodes"
            elif self.name == "azure":
                self.path = "appliedSpec.aksConfig.nodePools[].count"

class K8sCluster():
    '''Cluster Class

    Represents the Downstream clusters and holds cluster infos.

    Attributes
    ----------
    url: str
        The Cluster Upstream URL
    token: str
        Bearer-Token for Authentification
    debug_ : bool, default: False
        Debug Functions
    legacy : bool, default: False
        Accept Legacy Cluster "Vermittlung"
    '''

    def __init__(self, config: ClusterConfig, clusterType: ClusterType=ClusterType(name="rancher")) -> None: # path: str="/config/clusters.yaml"
        self.__config = config
        self.__clusters = [c["name"] for c in config.clusters]

    def __get_cluster(self, clusterName:str) -> dict :
        return next(item for item in self.__config.clusters if item["name"] == clusterName)

    def loadClusters(self) -> List[Cluster]:
        '''Loads the ClusterIDs and additional Cluster Information 

        Returns
        -------
        clusters : list

        Raises
        ------
        Cluster Endpoint Exception...
        '''
        try:
            response = get(f"{self.__config.clusterURL}/clusters", headers={"Authorization": f"Bearer {self.__config.apiToken}"}, timeout=2, verify=self.__config.verify) #self.__debug
            print("---init---\n self.__url:",self.__config.clusterURL,"\n self.__token:", self.__config.apiToken, "\nself.__qs:",self.__clusters, "\n self.__debug:",self.__config.debug )
            if self.__config.debug:
                print(response)
            if response.status_code == 200:
                clusters = response.json().get("data")
                qsClusters = []
                for c in clusters:
                    name = c["name"]
                    if any([s == name for s in self.__clusters]):
                        cluster_id = c["id"]
                        # get current nodes....
                        response_nodes = get(f"{self.__config.clusterURL}/clusters/{cluster_id}/nodes", headers={"Authorization": f"Bearer {self.__config.apiToken}"}, timeout=2, verify=self.__config.verify) #self.__debug
                        n_nodes = len(response_nodes.json().get("data"))
                        c_ = Cluster(name=c["name"], 
                                     id= cluster_id, 
                                     state= c["state"],
                                     n_nodes= n_nodes,
                                     environment=self.__get_cluster(name)["environment"],
                                     base = self.__get_cluster(name)["ingress"])
                        qsClusters.append(c_)
                print('qsClusters:', qsClusters)
                return qsClusters
        except:
            raise Exception(f"Cluster Endpoint {self.__config.clusterURL} not available...")