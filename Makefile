
#
# CAR_OCI_REGISTRY_HOST, CAR_OCI_REGISTRY_USERNAME and PROJECT_NAME are combined to define
# the Docker tag for this project. The definition below inherits the standard
# value for CAR_OCI_REGISTRY_HOST (=artefact.skao.int) and overwrites
# PROJECT_NAME to give a final Docker tag of artefact.skao.int/ska-ost-osd
#
CAR_OCI_REGISTRY_HOST ?= artefact.skao.int
CAR_OCI_REGISTRY_USERNAME ?= ska-telescope
PROJECT_NAME = ska-ost-osd
KUBE_NAMESPACE ?= ska-ost-osd
RELEASE_NAME ?= test

# include makefile to pick up the standard Make targets from the submodule

-include .make/helm.mk
-include .make/base.mk
-include .make/oci.mk
-include .make/k8s.mk
-include .make/python.mk
-include .make/tmdata.mk
# Set sphinx documentation build to fail on warnings (as it is configured
# in .readthedocs.yaml as well)
DOCS_SPHINXOPTS ?= -W --keep-going

docs-pre-build:
	poetry config virtualenvs.create false
	poetry install --no-root --only docs

.PHONY: docs-pre-build

IMAGE_TO_TEST = $(CAR_OCI_REGISTRY_HOST)/$(strip $(OCI_IMAGE)):$(VERSION)
K8S_CHART = ska-ost-osd-umbrella

 # Set cluster_domain to minikube default (cluster.local) in local development
# (CI_ENVIRONMENT_SLUG should only be defined when running on the CI/CD pipeline)
ifeq ($(CI_ENVIRONMENT_SLUG),)
K8S_CHART_PARAMS += --set global.cluster_domain="cluster.local"
endif

# For the test, dev and integration environment, use the freshly built image in the GitLab registry
ENV_CHECK := $(shell echo $(CI_ENVIRONMENT_SLUG) | egrep 'test|dev|integration')
ifneq ($(ENV_CHECK),)
K8S_CHART_PARAMS = --set ska-ost-osd.rest.image.tag=$(VERSION)-dev.c$(CI_COMMIT_SHORT_SHA) \
	--set ska-ost-osd.rest.image.registry=$(CI_REGISTRY)/ska-telescope/ost/ska-ost-osd
endif

# For the staging environment, make k8s-install-chart-car will pull the chart from CAR so we do not need to
# change any values
ENV_CHECK := $(shell echo $(CI_ENVIRONMENT_SLUG) | egrep 'staging')
ifneq ($(ENV_CHECK),)
endif

# unset defaults so settings in pyproject.toml take effect
PYTHON_SWITCHES_FOR_BLACK =
PYTHON_SWITCHES_FOR_ISORT =
PYTHON_SWITCHES_FOR_PYLINT =

# Restore Black's preferred line length which otherwise would be overridden by
# System Team makefiles' 79 character default
PYTHON_LINE_LENGTH = 88

# Set python-test make target to run unit tests and not the component tests
PYTHON_TEST_FILE = tests/unit/


# include your own private variables for custom deployment configuration
-include PrivateRules.mak

REST_POD_NAME=$(shell kubectl get pods -o name -n $(KUBE_NAMESPACE) -l app=ska-ost-osd,component=rest | cut -c 5-)

rest: ## start OSD REST server
	docker run --rm -p 5000:5000 --name=$(PROJECT_NAME) $(IMAGE_TO_TEST) gunicorn --chdir src \
		--bind 0.0.0.0:5000 --logger-class=ska_ost_osd.rest.wsgi.UniformLogger --log-level=$(LOG_LEVEL) ska_ost_osd.rest.wsgi:app

# install helm plugin from https://github.com/helm-unittest/helm-unittest.git
k8s-chart-test:
	mkdir -p charts/build; \
	helm unittest charts/ska-ost-osd/ --with-subchart \
		--output-type JUnit --output-file charts/build/chart_template_tests.xml

dev-up: K8S_CHART_PARAMS = \
	--set ska-ost-osd.rest.image.tag=$(VERSION) \
	--set ska-ost-osd.rest.ingress.enabled=true
dev-up: k8s-namespace k8s-install-chart k8s-wait ## bring up developer deployment

dev-down: k8s-uninstall-chart k8s-delete-namespace  ## tear down developer deployment

osd-pre-release:

	@./src/ska_ost_osd/osd/resource/release.sh $(VERSION)
