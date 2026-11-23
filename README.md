SKA Observatory Static Data
===========================

The Observatory Static Data (OSD) is a Python library, and the tmdata files it reads,
used by the Observatory Support Tools such as the PHT and ODT. The idea of OSD is to provide a single source of truth that is used to configure the science domain behavior of each tool.

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

Install dependencies with uv and activate the virtual environment

```
uv sync --all-groups
source .venv/bin/activate
```

Execute the test suite and lint the project with:

```
make python-test
make python-lint
```

Reformat the code and apply lint autofixes with:

```
make python-format
```

# Publish tmdata

The tmdata on `main` is published to the Central Artefact Repository by the manual `tmdata-publish` job of the `main` pipeline, and read as `car:ost/ska-ost-osd?main`. See [Publishing Data](https://developer.skao.int/projects/ska-ost-osd/en/latest/api/osd/publishing.html).

# Documentation

[![Documentation Status](https://readthedocs.org/projects/ska-telescope-ska-ost-osd/badge/?version=latest)](https://developer.skao.int/projects/ska-ost-osd/en/latest/?badge=latest)

Documentation can be found in the ``docs`` folder. To build docs, install the
documentation specific requirements:

```
uv sync --group docs
```

and build the documentation (will be built in docs/build folder) with

```
make docs-build html
```
