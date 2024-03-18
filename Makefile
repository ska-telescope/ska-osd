#
# CAR_OCI_REGISTRY_HOST, CAR_OCI_REGISTRY_USERNAME and PROJECT_NAME are combined to define
# the Docker tag for this project. The definition below inherits the standard
# value for CAR_OCI_REGISTRY_HOST (=artefact.skao.int) and overwrites
# PROJECT_NAME to give a final Docker tag of artefact.skao.int/ska-oso-osd
#
CAR_OCI_REGISTRY_HOST ?= artefact.skao.int
CAR_OCI_REGISTRY_USERNAME ?= ska-telescope
PROJECT_NAME = ska-oso-osd
KUBE_NAMESPACE ?= ska-oso-osd
RELEASE_NAME ?= test

-include .make/base.mk
-include .make/python.mk
# Set sphinx documentation build to fail on warnings (as it is configured
# in .readthedocs.yaml as well)
DOCS_SPHINXOPTS ?= -W --keep-going

docs-pre-build:
	poetry config virtualenvs.create false
	poetry install --no-root --only docs

.PHONY: docs-pre-build

IMAGE_TO_TEST = $(CAR_OCI_REGISTRY_HOST)/$(strip $(OCI_IMAGE)):$(VERSION)

# For the test, dev and integration environment, use the freshly built image in the GitLab registry
ENV_CHECK := $(shell echo $(CI_ENVIRONMENT_SLUG) | egrep 'test|dev|integration')
ifneq ($(ENV_CHECK),)
K8S_CHART_PARAMS = --set ska-oso-osd.rest.image.tag=$(VERSION)-dev.c$(CI_COMMIT_SHORT_SHA) \
	--set ska-oso-osd.rest.image.registry=$(CI_REGISTRY)/ska-telescope/oso/ska-oso-osd
endif

# Restore Black's preferred line length which otherwise would be overridden by
# System Team makefiles' 79 character default
PYTHON_LINE_LENGTH = 88


# include makefile to pick up the standard Make targets from the submodule

-include .make/oci.mk
-include .make/k8s.mk

-include .make/helm.mk

# include your own private variables for custom deployment configuration
-include PrivateRules.mak
