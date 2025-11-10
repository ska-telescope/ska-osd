
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

##
SKA_K8S_TOOLS_BUILD_DEPLOY ?= $(CAR_OCI_REGISTRY_HOST)/ska-cicd-k8s-tools-build-deploy:0.14.1
K8S_TEST_IMAGE_TO_TEST=$(SKA_K8S_TOOLS_BUILD_DEPLOY)
# The source code is used in the tests, so we set the PYTHONPATH in the tests to the location
# the source is copied into so that the imports work
PYTHONPATH = /src


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

openapi:
	python -c "from docs.openapi.export_openapi import export_openapi; export_openapi()"

# include your own private variables for custom deployment configuration
-include PrivateRules.mak

REST_POD_NAME=$(shell kubectl get pods -o name -n $(KUBE_NAMESPACE) -l app=ska-ost-osd,component=rest | cut -c 5-)


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

	@./src/ska_ost_osd/scripts/release.sh $(VERSION)

CI_MERGE_REQUEST_SOURCE_BRANCH_NAME := $(shell cat tmdata/version_mapping/latest_release.txt)

osddata-do-publish:
	@echo "tmdata-publish: package to publish: $(TMDATA_PKG) version: $(VERSION) in: $(TMDATA_OUT_DIR)"
	@. $(TMDATA_SUPPORT); publishTMData "$(TMDATA_SRC_DIR)" "$(TMDATA_OUT_DIR)" `git rev-parse HEAD` "${CI_COMMIT_TAG}" "${CI_COMMIT_BRANCH}" "${CI_MERGE_REQUEST_SOURCE_BRANCH_NAME}"
