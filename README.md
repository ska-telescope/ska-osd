SKA Observatory Static Data Services
=====================================

The Observatory Static Data Services is the server component of the
Observatory Support Tools. It provides the web services used by the OSO tools such as PPT and ODT.The idea of OSD is to provide a single source of truth that is used to configure the science domain behavior of each tool.

# Quick start
To clone this repository, run

```
git clone --recurse-submodules git@gitlab.com:ska-telescope/ost/ska-ost-osd.git
```

To refresh the GitLab Submodule, execute below commands:

```
git submodule update --recursive --remote
git submodule update --init --recursive
```

### Build and test

Install dependencies with Poetry and activate the virtual environment

```
poetry install
poetry shell
```

To build a new Docker image for the OSD, run

```
make oci-build
```

Execute the test suite and lint the project with:

```
make python-test
make python-lint
```

To run a helm chart unit tests to verify helm chart configuration:

```
helm plugin install https://github.com/helm-unittest/helm-unittest.git
make k8s-chart-test
```

### Deploy to Kubernetes

Install the Helm umbrella chart into a Kubernetes cluster with ingress enabled:

```
make k8s-install-chart
```

The Swagger UI should be available external to the cluster at `http://<KUBE_HOST>/<KUBE_NAMESPACE>/osd/api/<MAJOR_VERSION>/ui/ and the API accesible via the same URL.

If using minikube, `KUBE_HOST` can be found by running `minikube ip`. 
`KUBE_NAMESPACE` is the namespace the chart was deployed to, likely `ska-ost-osd`

To uninstall the chart, run

```
make k8s-uninstall-chart
```

# Deployments from CICD

### Deploying to non-production environments

There are 3 different environments which are defined through the standard pipeline templates. They need to be manually triggered in the Gitlab UI.

1. `dev` - a temporary (4 hours) deployment from a feature branch, using the artefacts built in the branch pipeline
2. `integration` - a permanent deployment from the main branch, using the latest version of the artefacts built in the main pipeline
3. `staging` - a permanent deployment of the latest published artefact from CAR

To find the URL for the environment, see the 'info' job of the CICD pipeline stage, which should output the URL alongside the status of the Kubernetes pods.
Generally the API URL should be available at  `https://k8s.stfc.skao.int/$KUBE_NAMESPACE/osd/api/v1`


## Flask
To start the Flask server run the following command in a terminal bash prompt

```
python src/ska_ost_osd/rest/wsgi.py
```

Alternatively use the following command

```
make rest
```

# Documentation

[![Documentation Status](https://readthedocs.org/projects/ska-telescope-ska-ost-osd/badge/?version=latest)](https://developer.skao.int/projects/ska-ost-osd/en/latest/?badge=latest)

Documentation can be found in the ``docs`` folder. To build docs, install the
documentation specific requirements:

```
pip3 install sphinx sphinx-rtd-theme recommonmark sphinxcontrib-openapi mistune==0.8.4
```

and build the documentation (will be built in docs/build folder) with

```
make docs-build html
```
