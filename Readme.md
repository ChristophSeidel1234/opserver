# OPServer by infologistix
## Description
OPServer is a continuous automated quality assurance system and as cloud-native solution designed to verify the functionality of multi-cluster Kubernetes platforms. In addition to the usual observability, it enables the examination of various functionalities. For instance, it can validate external calls and calls to external targets.


## Metrics
The container exports the metrics to `/metrics`

## Configuration for the Docker image
The values in `config.yaml` must be adjusted for the configuration.

### Values
| Key | Type | Default | Description |
|-----|------|---------|-------------|
| apiToken | string | mandatory | Rancher API token |
| baseIngress | string | mandatory | base ingress to access cluster |
| clusterURL | string | mandatory | Rancher URL |
| clusters | dict | mandatory | key is the cluster name and value the base |
| debug | bool | False | True/False |
| proxy | string | False | True/False |
| verify | string | False | verify SSL certificate |

## Usage
The directory `src` contains the python source code needed to build the docker image. The directory `opserver` contains the helm chart file structure

### Local test
To build the docker image, the values in `config.yaml` must be adjusted at first. Then the following commands can be executed.
Line 1 builds the image, line 2 starts the container and leads into the container. Line 3 must be called within the container. 

```bash
$ docker build . -f Dockerfile -t qs-automator:test
$ docker run -it --rm qs-automator:test sh
$ python3 main.py
```

### Install with helm
1. Build and push the docker image
```bash
$ docker build . -f Dockerfile -t qs-automator:test
$ docker push qs-automator:test
```
2. Create the namespace quality-assurance and install opserver
```bash
$ helm install opserver ./opserver --namespace quality-assurance --create-namespace --wait
```
### Uninstall with helm
```bash
$ helm uninstall opserver --namespace quality-assurance
```