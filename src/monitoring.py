#!/bin/python

import re
from typing import List
from requests import get
from faillog import QSLog
from clusters import Cluster

class Monitor():
    '''CHeck QS Monitoring

    Attributes
    ----------
    url: str
        the cluster rancher URL
    log : QSLog
        Logging Descriptor
    debug: bool, default: False
        debug mechanism
    '''
    def __init__(self, url:str,  log: QSLog, debug_:bool=False, verify:bool=False) -> None:
        self.__debug = debug_
        self.__dashboards = ["Tester-Status-Neu Rancher / Node"] 
        self.__log = log
        self.__verify = verify

    def runQS(self, clusters:List[Cluster]) -> None:
        '''
        Main Handler Function for QS
        '''
        for cluster in clusters:
            __cluster = f"{cluster.base}/monitoring/"
            print("--------\n[ \033[1;35mChecking\033[0m ] {}".format(cluster.name))
            urls = [__cluster]
            for url in urls:
                # prometheus
                prometheus = "{}prometheus/".format(url)
                self.__log.write("{}\t {}".format(self.__checkStatus(prometheus)[0], prometheus))
                # alertmanager
                alertmanager = "{}alertmanager/".format(url)
                self.__log.write("{}\t {}".format(self.__checkStatus(alertmanager)[0], alertmanager))
                # grafana
                grafana = "{}grafana/".format(url)
                dashboards = "{}api/search".format(grafana)
                status = self.__checkStatus(grafana)
                if status[1] == 200 and not self.__checkDashboards(dashboards):
                    self.__log.write("[\033[1;33mWARN\033[0m]\t\t {} Dashboards Missing...".format(grafana))
                else:
                    self.__log.write("{}\t {}".format(status[0], grafana))

    def __checkStatus(self, url: str) -> list[str,int]:
        '''
        Checking the Status of Dashboard URLS

        Params
        ------
        url : str
            the url of the dashboard
        
        Returns
        -------
        list : [str, int]
            Formatted Response and Response Code
        '''
        if self.__debug:
            print(f"GET {url}")
        # add a catch statement, if anything goes wrong at this point
        try:
            response = get(url, verify=self.__verify).status_code
            if response == 200:
                return ["[ \033[0;32mOK\033[0m ]\t", response]
            # extract 500+ as warning -> bad Gateway -> fixable
            elif response%400 > 99:
                return ["[\033[1;33mWARN\033[0m]\t", response]
            else:
                return ["[\033[0;31mFailed\033[0m]", response]
        except Exception as e:
            print(e)
        return ["[\33[0;31mFailed\033[0m]", f"URL {url} not found."]

    def __checkDashboards(self, url: str) -> bool:
        '''
        Checking Grafana Dashboard List

        Params
        ------
        url : str
            the url to get
        
        Returns
        -------
        bool
            Dashboards required are there or not :)
        '''
        if self.__debug:
            print(f"GET {url}")
        # add a catch statement, if anything goes wrong at this point
        try:
            response = get(url, verify=self.__verify)
            if self.__debug:
                print(response.json())
            else:
                if any(e["title"] in self.__dashboards for e in response.json()):
                    return True
        except Exception as e:
            print(e)    
        return False
        
            