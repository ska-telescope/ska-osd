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

### Release a new version

This is a very crucial part for OSD, without this some functionality may break and exceptions and errors will be raised.

Failing to run this command before releasing a new version may cause test cases to fail. This command ensures all necessary pre-release checks and configurations are properly set up.

Run Below command from Command line.

```
make osd-pre-release
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

# Configuring Semantic Validation

The semantic validation API endpoint `POST /semantic_validate` can be enabled
or disabled by configuring the validation strictness level:

- For local development, set the `VALIDATION_STRICTNESS` environment variable
- For deployments, set the `validation_strictness` parameter in the Helm
  `values.yaml` file

When enabled, semantic validation will return 200 for a semantically valid
request, otherwise 400 with a list of semantic errors. When disabled, semantic
validation will always return 200 with a message that semantic validation is
disabled.

The validation strictness level is used across multiple OSO services and also
configures schema validation strictness in `ska-telmodel`. A summary of the
possible validation strictness levels and how they configure both syntactic
validation in `ska-telmodel` and semantic validation in `ska-ost-osd` is given
below:

| Validation Strictness | Syntactic Validation (TelModel Schemas) | Semantic Validation (OSD) |
|-----------------------|-----------------------------------------|---------------------------|
| 0                     | Permissive Warnings                     | Disabled                  |
| 1                     | Permissive Errors & Strict Warnings     | Disabled                  |
| 2                     | Permissive & Strict Errors              | Enabled                   |

> ⚠️ **Warning**
> From version 1.24.0, `ska-telmodel` schema validation strictness level 0 will
> become obsolete. If validation strictness is configured to 0, schema
> validation will instead run at validation strictness level 1. Future versions
> of `ska-telmodel` may drop all validation strictness levels entirely, in which
> case the configuration of semantic validation is also liable to change.

# Publish tmdata

Now OSD is handling releases separately for tmdata and ska-ost-osd codebase. 
User can now update tmdata with the help of [ OSD UI editor](https://k8s.stfc.skao.int/ska-oso-integration/osd) and publish it separately on artefact repository with enabling `push_to_gitlab` environment variable to "1".

`push_to_gitlab` environment variable configured into values.yaml in chart directory
which allow restrict tmdata publish on artefact. Default set as "0" for local environment.

`push_to_gitlab` = 0 ## for local environment, it won't publish tmdata on artefact repository.

`push_to_gitlab` = 1 ## it will publish tmdata on artefact repository.

To view tmdata releases, [ Click here](https://gitlab.com/ska-telescope/ost/ska-ost-osd/-/blob/main/tmdata/version_mapping/latest_release.txt?ref_type=heads).

It's not recommended  to set this flag value as "1" while doing testing on local environment.

# Install charts

```
make k8s-install-chart
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
