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

OSD_VALIDATOR_VERSION ?= 8.0.0
SKA_PYPI_INDEX ?= https://artefact.skao.int/repository/pypi-internal/simple

# Validates with a released ska-ost-osd from the CAR, isolated from this checkout,
# so the data is checked by the code that deployments read it with
tmdata-validate: ## validate the tmdata files with a released ska-ost-osd
	uv tool run --isolated --no-config --index $(SKA_PYPI_INDEX) \
		--from "ska-ost-osd==$(OSD_VALIDATOR_VERSION)" \
		osd-validate-tmdata $(TMDATA_SRC_DIR)

# Where tmdata-publish uploads the tmdata, as .make/.make-tmdata-support builds it
TMDATA_CAR_URL ?= $${CAR_TMDATA_REPOSITORY_URL:-$${CAR_RAW_REPOSITORY_URL%internal}telmodel}/$(CI_SERVER_HOST)/$(CI_PROJECT_PATH)/$(TMDATA_SRC_DIR)
TMDATA_PUBLISHED_REF ?= $(CI_COMMIT_REF_NAME)

# Check the tmdata published for TMDATA_PUBLISHED_REF matches the local tmdata
tmdata-check-published: ## check the tmdata published for TMDATA_PUBLISHED_REF is the local tmdata
	@set -e; \
	published=$$(mktemp -d); \
	trap 'rm -rf "$$published"' EXIT; \
	status=$$(curl -sS -o "$$published/commit" -w '%{http_code}' "$(TMDATA_CAR_URL)/$(TMDATA_PUBLISHED_REF)"); \
	case "$$status" in \
		200) ;; \
		404) echo "Nothing published for $(TMDATA_PUBLISHED_REF) yet"; exit 1;; \
		*) echo "Can't read what is published for $(TMDATA_PUBLISHED_REF): HTTP $$status"; exit 1;; \
	esac; \
	commit=$$(cat "$$published/commit"); \
	case "$$commit" in \
		*[!0-9a-f]*|"") echo "Not a commit: $$commit"; exit 1;; \
	esac; \
	status=$$(curl -sS -o "$$published/tmdata.tar.gz" -w '%{http_code}' "$(TMDATA_CAR_URL)/~$$commit/tmdata.tar.gz"); \
	case "$$status" in \
		200) ;; \
		404) echo "$(TMDATA_PUBLISHED_REF) points at $$commit, but no tmdata is published for that commit"; exit 1;; \
		*) echo "Can't read the tmdata published for $$commit: HTTP $$status"; exit 1;; \
	esac; \
	tar -xzf "$$published/tmdata.tar.gz" -C "$$published"; \
	if differences=$$(diff -rq "$$published/$(TMDATA_SRC_DIR)" "$(TMDATA_SRC_DIR)"); then \
		echo "The tmdata published for $(TMDATA_PUBLISHED_REF) (commit $$commit) matches the local tmdata"; \
	else \
		echo "$$differences" | sed "s|$$published/|published/|g"; \
		echo "The tmdata published for $(TMDATA_PUBLISHED_REF) (commit $$commit) doesn't match the local tmdata"; \
		exit 1; \
	fi

# include your own private variables for custom configuration
-include PrivateRules.mak
