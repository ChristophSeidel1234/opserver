# OPServer by infologistix

OPServer is a continuous automated quality assurance system and as cloud-native solution designed to verify the functionality of multi-cluster Kubernetes platforms. In addition to the usual observability, it enables the examination of various functionalities. For instance, it can validate external calls and calls to external targets.

## Note

We are currently in the beta phase and it is not yet possible to contribute. However, this should be possible in the future. If you would still like to share an idea with us, please send an e-mail to <cloudengineering@infologistix.de>.

## Metrics

The container exports the metrics to `/metrics`

## Configuration for the Docker image

The values in `config.yaml` must be adjusted for the configuration.

### Values

#### Config

The `config.yaml` speficies the configuration of the opserver plugin.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `clusterURL` | string | mandatory | Rancher URL |
| `clusters` | dict | mandatory | Clusters as Dict <br> `{ name: "cluster-name", environment: ["env1", "env2"], ingress: "ingress.domain.com" }` |
| `apiToken` | string | `""` | Rancher API token |
| `debug` | bool | `False` | True/False |
| `proxy` | string | `True` | Use Rancher Proxy for Grafana/Prometheus |
| `verify` | string | `True` | verify SSL certificate |

The API-Token can be set as Environment-Variable. This takes presedence over the setting in `config.yaml`.

#### Limits

The `limits.yaml` will specify the corresponding limits for the management scraping while searching for the required performance values.
To adapt to new changes, simply edit the defaults in `config/limits.yaml` or supply during runtime.

## Usage

The directory `src` contains the python source code needed to build the docker image. The directory `charts/opserver` contains the helm chart file structure

### Local test

To build the docker image, the values in `config.yaml` must be adjusted at first. Then the following commands can be executed.

```bash
docker build . -f Dockerfile.debian -t qs-automator:test
docker run -it --rm qs-automator:test sh
python3 main.py
```

### Install with helm

Build and push the docker image

```bash
docker build . -f Dockerfile -t qs-automator:test
docker push qs-automator:test
```

Create the namespace quality-assurance and install opserver

```bash
helm install opserver ./charts/opserver --namespace quality-assurance --create-namespace --wait
```

### Uninstall with helm

```bash
helm uninstall opserver --namespace quality-assurance
```

## License

Copyright (c) infologistix GmbH

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

<http://www.apache.org/licenses/LICENSE-2.0>

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
