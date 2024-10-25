#!/bin/python

from argparse import ArgumentParser, Namespace
from datetime import datetime
import warnings
from codetiming import Timer
from typing import List
from dataclasses import asdict
from requests import get
from requests.exceptions import ConnectTimeout
from clusters import K8sCluster, Cluster, ClusterConfig
from manager import Manager, ResourceLimits
from faillog import QSLog
from monitoring import Monitor
from explorer import Dashboard
from security import secure_headers
import yaml
import os
import time
from flask import Flask, render_template
import threading
from prometheus_client import make_wsgi_app, Gauge, Counter, Histogram
from werkzeug.middleware.dispatcher import DispatcherMiddleware


updateLog:QSLog
app = Flask(__name__, static_url_path='/static')
g_tests = Gauge("opserver_observed_test", "observed test metrics", ['type'])
g_total_tests = Gauge("opserver_total_tests", "total number of tests to perform")
c_test = Counter("opserver_test_ran", "Increasing number of tests, opserver ran")
h_duration = Histogram("opserver_test_duration_seconds", "Duration of each test run",
                       buckets=(30, 45, 60, 75, 90, 120, 135, 150, 165, 180, 240, 300, float("inf")))
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {'/metrics': make_wsgi_app()})
# Fix Problem that the assets are tried to load from Domain Root
if os.getenv("APPLICATION_ROOT"):
    app.config['APPLICATION_ROOT'] = os.getenv("APPLICATION_ROOT")

class QS():
    def __init__(self, clusters: List[Cluster], config:ClusterConfig, limits: ResourceLimits) -> None:
        self.__clusters = clusters
        self.__token = config.apiToken
        self.__url = config.clusterURL
        self.__limits = limits
        self.__debug = config.debug
        self.__proxy = config.proxy
        self.__verify = config.verify
        self.__log = QSLog()

    @Timer(name="Complete Run")
    @h_duration.time()
    def run(self, step=None):
        if step==None:
            self.__managing()
            self.__dashboard()
            self.__monitoring()
        else:
            if step == 1:
                self.__managing()
            elif step == 2:
                self.__dashboard()
            elif step == 3:
                self.__monitoring()
            else:
                raise NotImplementedError()
        self.__log.summarize()
        global updateLog
        updateLog = self.__log
        g_tests.labels("success").set(len(updateLog.success))
        g_tests.labels("warning").set(len(updateLog.warn))
        g_tests.labels("failed").set(len(updateLog.fails))
        g_total_tests.set(updateLog.total)
        c_test.inc()


    @Timer(name="QS from Dashboards")
    def __dashboard(self):
        print("--------\nSTEP 2 - Dashboard Cluster-Explorer\nrunning QS...")
        Dashboard(url=self.__url, token=self.__token, log=self.__log, debug_=self.__debug, proxy=self.__proxy, verify=self.__verify).runQS(self.__clusters)  

    @Timer(name="QS from Cluster Management")
    def __managing(self):
        print("--------\nSTEP 1 - Rancher Cluster Manager\nrunning QS...")
        Manager(url=self.__url, token=self.__token, log=self.__log, limits=self.__limits, debug_=self.__debug, verify=self.__verify).runQS(self.__clusters)

    @Timer(name="QS from Monitoring")
    def __monitoring(self):
        print("--------\nSTEP 3 - Monitoring\nrunning QS...")
        Monitor(url=self.__url, log=self.__log, debug_=self.__debug, verify=self.__verify).runQS(self.__clusters)

def argParser() -> Namespace:
    parser = ArgumentParser(description="Cluster Exploration und Dashboard Verifikation - QS")
    #parser.add_argument("--token", "-t", dest="token", type=str, default=None, help='Token for registration on the cluster')
    #parser.add_argument("--cluster", "-c", dest="cluster", type=str, default=None, help='Rancher Cluster URL')
    #parser.add_argument("--debug", dest="debug", action="store_true", help="set to debugging mode")
    #parser.add_argument("--proxy", dest="proxy", action="store_false", default=True, help="Use Rancher Proxy and scrape that endpoint for testing")
    parser.add_argument("--path", type=str, dest="path", default="config/config.yaml", help="Path for Config yaml")
    args = parser.parse_args()
    print(f'args.path = {args.path}')
    return args

def readYAML(path: str):
    if os.path.exists(path):
        with open(path, "r") as f:
            conf = yaml.safe_load(f)
            return ClusterConfig(**conf)
    else:
        raise Exception("No Config Loaded")

def buildResponse():
    if not updateLog:
        return {
            "cluster": os.getenv("CLUSTER_URL"),
            "time": time.time(),
            "time_hr": time.strftime("%X %x"),
            "lastRun": None,
            "lastRun_hr": None,
            "fails": None,
            "warnings": None,
            "success": None,
            "summarize": None
        }
    return {
            "cluster": os.getenv("CLUSTER_URL"),
            "time": time.time(),
            "time_hr": time.strftime("%X %x"),
            "lastRun": updateLog.lastRun,
            "lastRun_hr": datetime.fromtimestamp(updateLog.lastRun).strftime("%X %x"),
            "fails": {
                "description": updateLog.fails,
                "count": len(updateLog.fails)
            },
            "warnings": {
                "description": updateLog.warn,
                "count": len(updateLog.warn)
            },
            "success": {
                "description": updateLog.success,
                "count": len(updateLog.success)
            },
            "summarize": {
                "total": updateLog.total,
                "relative": {
                    "fails": len(updateLog.fails)/updateLog.total,
                    "warnings": len(updateLog.warn)/updateLog.total,
                    "success": len(updateLog.success)/updateLog.total
                },
                "absolute": {
                    "fails": len(updateLog.fails),
                    "warnings": len(updateLog.warn),
                    "success": len(updateLog.success)
                }
            }
        }

def buildStatus():
    try:
        if updateLog:
            pass
        if updateLog.fails:
            headers = {
                "status": 0,
                "status_info" : f"FAILED: QS has failed: {updateLog.fails}" 
            }
        elif updateLog.warn:
            headers = {
                "status": 0,
                "status_info" : f"WARNING: QS raised Warnings: {updateLog.warn}" 
            }
        else:
            headers = {
                "status": 1,
                "status_info" : "HEALTHY: QS Completed sucessfully"
            }
    except:
        headers = {
            "status": 0,
            "status_info" : "UNHEALTHY: Service ist not running"
        }
    return headers

@app.after_request
def set_security_headers(response):
    secure_headers().framework.flask(response)
    response.headers["X-Download-Options"] = "noopen"
    return response

@app.route("/")
@app.route("/summarize")
def summarizeAsHTML():
    headers = buildStatus()
    try:
        response = buildResponse()
        response["environment"] = response.get("cluster")
        response["summarize"]["relative"] = {k:f"{round(v*100,2)}%" for k,v in response["summarize"]["relative"].items()}
        return render_template("summarize.html", data=response), 200, headers
    except:
        print("except:", headers.get("status_info"), 200, headers)
        return headers.get("status_info"), 200, headers

@app.route("/v1/summarize")
def summarizeAsJSON():
    # JSON response
    return buildResponse()

@app.route("/status")
def clusterStatus():
    headers = buildStatus()
    return headers.get("status_info"), 200, headers


def apiServer():
    app.config.update(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        STATIC_ROOT=''
    )
    app.run(host="0.0.0.0", port=8080, debug=False)

if __name__=="__main__":
    args = argParser()
    config = readYAML(args.path)
    try:
        clusters = K8sCluster(config=config).loadClusters()
    except ConnectTimeout:
        print(f"Connection to {config.clusterURL} failed. Host not reachable!")
        exit()
    #just wait till everything is up & running and start api-server
    if not config.debug:
        threading.Thread(target=apiServer, daemon=True).start()
    else:
        print(clusters)
        print("Debugging Mode. Does not start the API Server")
        print([asdict(cluster) for cluster in clusters])
        warnings.simplefilter("ignore")
        warnings.catch_warnings()
    lastTime = 0
    while True:
        # run every 1 minute... 
        if time.time()-lastTime > 60:
            lastTime = time.time()
            print(f"\nStarting new Testcycle @ {time.strftime('%a, %d.%m.%y %H:%M:%S')}\n")
            try:
                clusters = K8sCluster(config=config).loadClusters()
            except ConnectTimeout:
                print(f"Connection to {config.clusterURL} failed. Host not reachable!")
                exit()

            print("clusters:", clusters)
            qs = QS(clusters=clusters, config=config, limits=ResourceLimits())
            qs.run()
        if config.debug:
            break