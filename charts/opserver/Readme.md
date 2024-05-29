# Helm Chart Opserver

## TL;DR

```console
git clone git@github.com:infologistix/opserver.git
cd opserver/charts/opserver

kubectl create namespace opserver
helm install opserver . --namespace opserver
```

## Introduction

OPServer is a continuous automated quality assurance system and as cloud-native solution designed to verify the functionality of multi-cluster Kubernetes platforms. In addition to the usual observability, it enables the examination of various functionalities. For instance, it can validate external calls and calls to external targets.

## Installing the Chart

To install the chart with the release name `opserver`:

```console
kubectl create namespace opserver
helm install opserver . --namespace opserver
```

## Uninstalling the Chart

To uninstall/delete the `opserver` Helm chart:

```console
helm uninstall opserver --namespace opserver
```

The command removes all the Kubernetes componentes associated with the chart and deletes the release.

## Configuration

The following table lists the configurable parameters of the Opserver chart and their default values.

### General parameters

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| config.apiToken | string | `"secret-token"` | the rancher API-Token to be supplied |
| config.config | object | `{"clusterURL":"https://rancher-url/v3","clusters":[{"environment":["cluster"],"ingress":"my-cluster.domain.com","name":"my-cluster"}]}` | Config.yaml Sample for the Application. |
| config.limits | object | `{"istioIngressgateway":{"cpu":2,"memory":"1Gi"},"rancherMonitoringPrometheus":{"cpu":1,"memory":"3000Mi"}}` | limit.yaml Sample for the Application set the Limits for the artefacts |
| image | object | `{"imagePullSecrets":[],"pullPolicy":"Always","registry":"","repository":"qs-automator","tag":"test"}` | Configure custom image specs |
| image.imagePullSecrets | list | one or more of `[{"name": "registry"}, {"name": "docker", "registry": "docker.io", "username": "user", "password": "password"}]` | Image Pull Secrets. If only Name is registered. If registry, username, password is set, will be generating a new docker secret |
| image.pullPolicy | string | `"Always"` | PullPolicy to pull the image |
| image.registry | string | `""` | Custom registry to use |
| image.repository | string | `"qs-automator"` | Image Repository to use |
| image.tag | string | `"test"` | Image Tag Specification |
| ingress.config | object | `{"gateways":[],"hosts":["ingress.com"],"paths":["/opserver"]}` | Ingress Configuration |
| ingress.config.gateways | list | "istio-system/istio-ingress-gateway" | Capability to set Custom gateways |
| ingress.config.hosts | list | `["ingress.com"]` | The Hosts (domains) in the Virtual Service |
| ingress.config.paths | list | `["/opserver"]` | path based Routing will strip leading and trailing / and add them where it will be needed |
| ingress.enabled | bool | `true` | Enable Ingress via VirtualServices |
| pod.annotations | object | `{"proxy.istio.io/conifg":"{holdApplicationUntilProxyStarts: true}","sidecar.istio.io/rewriteAppHTTPProbers":"true"}` | extra pod annotations |
| pod.labels | object | `{}` | extra pod labels |
| pod.resources | object | `{"limits":{"cpu":"128m","memory":"128Mi"},"requests":{"cpu":"64m","memory":"64Mi"}}` | pod default resources |
| securityContext | object | `{"runAsUser": 1668442480, "runAsGroup": 1668442480, "fsGroup": 1668442480, "fsGroupChangePolicy": "OnRootMismatch"}` | Set the Security Context |
| service.port | int | `8080` | The services Port |
| serviceAccount.annotations | object | `{}` | Annotations to add to the service account |
| serviceAccount.create | bool | `true` | Specifies whether a service account should be created |
| serviceAccount.name | string | If not set, a name is generated using the fullname template | The name of the service account to use. |
| serviceMonitor | object | `{"customLabels":{"label":"test"},"enabled":false}` | Opserver is Capable to supply metrics |
| serviceMonitor.customLabels | object | `{"label":"test"}` | custom Labels to suppliy for label matching prometheus scraping |
| serviceMonitor.enabled | bool | `false` | enable ServiceMonitor endpoint |

Configure the respective values and install the chart.

```console
helm install opserver . --namespace opserver -v values.yaml
```

## Opserver is secure by default

Out default configuration strives to be as secure as possible. Beacaus of that, Opserver will run as non-root and be secure-by-default:

```yaml
serviceaccountName: opserver
securityContext:        
    runAsUser: 1668442480
    runAsGroup: 1668442480
    fsGroup: 1668442480
    fsGroupChangePolicy: "OnRootMismatch"

podSecurityContext:            
    allowPrivilegeEscalation: false
    capabilities:
        drop:
        - ALL
    privileged: false
    readOnlyRootFilesystem: true
    runAsNonRoot: true
```
