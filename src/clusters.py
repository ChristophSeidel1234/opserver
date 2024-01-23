#!/bin/python

from typing import List
from requests import get
from dataclasses import dataclass
#from pprint import pprint
#import yaml
#import re
#import os

#def clusters(path: str):
#    if os.path.exists(path):
#        with open(path, "r") as f:
#            clusters = yaml.safe_load(f)
#    else:
#        clusters = []
#    return clusters

@dataclass
class Cluster():
    name:str # Name
    id: str # Rancher ClusterID
    state: str # State
    n_nodes: int # number of Nodes
    #location: str # Standort Label zB
    #environment: str # Prod, Dev, Test, ...
    base: str="" # Ingress Base Domain für Dinge auf dem Cluster

    #def destruct_cluster(self, cluster):
    #    r=r'i-(?P<location>\w{3})-(?P<cluster>.*)'
    #    #return re.search(r, cluster).groups()
    #    return "name"

    #def __post_init__(self):
        # name = self.name.split("-")[-1]
    #    print('name:', self.name)
    #    name = self.name #self.destruct_cluster(self.name)[-1] or "prod-cluster" or "mycluster" # To Generalize
    #    name = name if name != "plattform" else "services"
    #    self.base = f"https://{name}-bapc-{self.location}.con.{self.environment}" # To Change or in config.yaml?

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

    def __init__(self, url: str, token: str, clusters: list, debug_=False, verify=False, clusterType: ClusterType=ClusterType(name="rancher")) -> None: # path: str="/config/clusters.yaml"
        self.__url=url
        self.__token=token
        self.__qs = clusters
        self.__debug = debug_
        self.__verify = verify 
        #self.__base = ""
        #self.__environment = environment #"idst.ibaintern.de" if "idst" in url else "dst.baintern.de" # To Change
        #self.__location = location #"vdt" if "vdt" in url else "thf" # To Change

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
            response = get(f"{self.__url}/clusters", headers={"Authorization": f"Bearer {self.__token}"}, timeout=2, verify=self.__verify) #self.__debug
            print("---init---\n self.__url:",self.__url,"\n self.__token:", self.__token, "\nself.__qs:",self.__qs, "\n self.__debug:",self.__debug )
            if self.__debug:
                print(response)
            if response.status_code == 200:
                clusters = response.json().get("data")
                qsClusters = []
                for c in clusters:
                    name = c["name"]
                    if any([s == name for s in self.__qs]):
                        cluster_id = c["id"]
                        response_nodes = get(f"{self.__url}/clusters/{cluster_id}/nodes", headers={"Authorization": f"Bearer {self.__token}"}, timeout=2, verify=self.__verify) #self.__debug
                        n_nodes = len(response_nodes.json().get("data"))
                        c_ = Cluster(name=c["name"], 
                                     id= cluster_id, 
                                     state= c["state"],
                                     # to be implemeted...
                                     # specific AKS config
                                     #n_nodes= sum([item["count"] for item in c["appliedSpec"]["aksConfig"]["nodePools"]]),
                                     n_nodes= n_nodes,
                                     base = self.__qs[name])
                        qsClusters.append(c_)
                print('qsClusters:', qsClusters)
                return qsClusters
        except:
            raise Exception(f"Cluster Endpoint {self.__url} not available...")