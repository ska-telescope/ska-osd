PROJECT_NAME = ska-ost-osd

# include makefile to pick up the standard Make targets from the submodule

-include .make/base.mk
-include .make/python-uv.mk
-include .make/tmdata.mk
# Set sphinx documentation build to fail on warnings (as it is configured
# in .readthedocs.yaml as well)
DOCS_SPHINXOPTS ?= -W --keep-going

PYTHON_RUNNER = uv run
DOCS_PYTHON_RUNNER = uv run python3

# Set python-test make target to run unit tests and not the component tests
PYTHON_TEST_FILE = tests/unit/

tmdata-validate: ## validate the tmdata files against the OSD storage models
	$(PYTHON_RUNNER) osd-validate-tmdata $(TMDATA_SRC_DIR)

# include your own private variables for custom configuration
-include PrivateRules.mak
