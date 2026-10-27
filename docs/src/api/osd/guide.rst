OSD Model
-------------------

In its simplest form OSD consists of a set of science domain configuration files that are required by the OSO tools.
These configuration files hold slowly changing information that is used to configure the science domain behavior of each tool.
E.g. tools such as the PPT and ODT can use the information for constructing GUIs and validating setups, the Planning Tool can use it to inform itself of the capabilities available.
The idea of OSD is to provide a single source of truth for these data.


.. contents::


Introduction
~~~~~~~~~~~~~
Here we have created 'Observatory Static Data (OSD) Module'.

For creating this framework there are some requirements and architecture have already provided.
These are as follows:

* `Observatory Static Data (OSD) <https://confluence.skatelescope.org/pages/viewpage.action?spaceKey=SWSI&title=Observatory+Static+Data>`_
* `OSD Documentation Confluence Page <https://confluence.skatelescope.org/display/SE/%5BDraft%5D+OSD+documentation>`_


Folder Structure
~~~~~~~~~~~~~~~~~

.. code-block:: bash

    tmdata
    ├── cycles
    │   ├── cycle_1.json
    │   └── cycle_<id>.json
    ├── ska1_low
    │   └── low_capabilities.json
    └── ska1_mid
        └── mid_capabilities.json


* `mid_capabilities.json <https://confluence.skatelescope.org/pages/viewpage.action?spaceKey=SWSI&title=Observatory+Static+Data>`_

* `low_capabilities.json <https://confluence.skatelescope.org/pages/viewpage.action?spaceKey=SWSI&title=Observatory+Static+Data>`_

.. note::

    Each observing cycle is stored in its own
    ``cycles/cycle_<id>.json`` file. The legacy ``observatory_policies.json``
    file remains at the root on main for backward compatibility with the old
    legacy version mapper.

Querying the OSD
~~~~~~~~~~~~~~~~~

``get_osd_using_tmdata`` (``ska_ost_osd.osd.osd``) returns the OSD data as a
dictionary, selected by cycle, telescope and array assembly. New code should use
the repository described in :doc:`python_api`, which returns the same data as
Pydantic models.

.. code-block:: python

    from ska_telmodel_client import TMData

    from ska_ost_osd.osd.common.constant import Telescope
    from ska_ost_osd.osd.osd import get_osd_using_tmdata

    tmdata = TMData(["car:ost/ska-ost-osd?7.0.0"], update=True)
    osd_data = get_osd_using_tmdata(tmdata, telescope=Telescope.MID, cycle_id=1)

===================    ============================================================
Parameters             Description
===================    ============================================================
tm_data                the TMData client to read the tmdata from
cycle_id               Cycle Id a integer value 1, 2, 3
telescope              ``Telescope.MID`` or ``Telescope.LOW``
array_assembly         AA0.5, AA1 or any Array Assembly
process_templates      whether to replace the ``subarray_templates`` patterns with
                       the templates, see `Subarray Template Support`_
===================    ============================================================


Response
~~~~~~~~~

.. code-block:: json

    {
    "observatory_policy": {
      "cycle_number": 1,
    "telescope_capabilities": []},
    "capabilities": {
      "mid": {},
      "low": {}}
    }


======================    ============================================================================================================
Keys                      Description
======================    ============================================================================================================
observatory_policy        file content of the selected ``cycles/cycle_<id>.json`` file
telescope_capabilities    value of ``telescope_capabilities`` in the selected cycle file
capabilities              key value pair of mid and low
Mid                       file content of ``mid_capabilities.json`` with ``basic_capabilities`` and ``Array Assembly`` AA0.5, AA1 etc
Low                       file content of ``low_capabilities.json`` with ``basic_capabilities`` and ``Array Assembly`` AA0.5, AA1 etc
======================    ============================================================================================================


Scenarios
~~~~~~~~~~

1. With no filters, it returns the complete OSD catalogue: every telescope's
   ``basic_capabilities`` together with all of its named array assemblies. No
   ``observatory_policy`` is included, since no ``cycle_id`` was selected.

2. With ``cycle_id``, it checks that the corresponding ``cycles/cycle_<id>.json``
   file exists, then uses that file's ``telescope_capabilities`` to select the array
   assembly of each telescope. The cycle file is returned as ``observatory_policy``.

3. With ``telescope``, it returns only that telescope; with ``array_assembly`` as
   well, only that array assembly.


Error Handling
```````````````

If the query is invalid, ``get_osd_using_tmdata`` raises a ``ValueError`` whose
argument is the list of error messages. For example:

* ``array_assembly`` without ``telescope``:

  .. code:: python

      Array assembly requires a capability.

* ``cycle_id`` and ``array_assembly`` without ``telescope``:

  .. code:: python

      Cycle_id and Array_assembly cannot be used together.

* an ``array_assembly`` that isn't the one the cycle offers for the telescope:

  .. code:: python

      Array assembly AA1 does not match capability mid in cycle 2. Expected AA2.

* a ``cycle_id``, ``telescope`` or ``array_assembly`` with no data, or a telescope
  that the cycle doesn't offer.


Publishing tmdata
~~~~~~~~~~~~~~~~~~

The tmdata is published to CAR with the same version as the Python package, so a
breaking change to the tmdata is released as a new major version. Consumers should
read a pinned version, such as ``car:ost/ska-ost-osd?7.0.0``, rather than ``main``.

It is published by the manual ``tmdata-publish`` job of the GitLab pipeline, which
runs:

.. code-block:: bash

    # Publish TMData to artifact repository
    make tmdata-publish

View TMData Releases
~~~~~~~~~~~~~~~~~~~~~

To view current TMData releases: `TMData Releases <https://gitlab.com/ska-telescope/ost/ska-ost-osd/-/blob/main/tmdata/version_mapping/latest_release.txt?ref_type=heads>`_


Manual tmdata Release Steps
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Create a JIRA issue and the branch

    1st: Create a new issue on the Release Management Jira Project with a summary of your release, and set it to “IN PROGRESS”.

    2nd: Create and checkout a new rel-XXX-release-v-1-2-2 branch (where REL-XXX is your Jira issue.)

2. Check the Current Version

.. code:: bash

    make show-version

3. Bump the Version

.. code:: bash

    make bump-patch-release

4. Set the Release

* `For remaining release steps click here <https://developer.skao.int/en/latest/tutorial/release-management/automate-release-process.html>`_

.. warning::

    This is a very crucial part for OSD, without this some functionality may break and exceptions and errors will be raised.


OSD Integration
~~~~~~~~~~~~~~~

This section explains how to integrate and use the **ska-ost-osd** package in your project.

Installation
------------

Add the following entry under the ``[project]`` ``dependencies`` list in your ``pyproject.toml``:

.. code-block:: toml

    [project]
    dependencies = [
        "ska-ost-osd>=<majorversion>,<<nextmajorversion>",
    ]

This will ensure that a compatible version of the ``ska-ost-osd`` package is installed.

Usage
-----

See :doc:`python_api` for reading the OSD through the repository and the views.

Subarray Template Support
~~~~~~~~~~~~~~~~~~~~~~~~~

OSD now supports subarray templates through the ``subarray_templates`` field in array assembly configurations. This feature enables dynamic template loading and processing for different telescope configurations.

Configuration
-------------

Each array assembly (AA0.5, AA1, AA2) can specify subarray templates using wildcard patterns:

.. code-block:: json

    {
        "AA0.5": {
            "subarray_templates": ["*_AA0.5"],
            "other_config": "..."
        },
        "AA1": {
            "subarray_templates": ["*_AA1"],
            "other_config": "..."
        },
        "AA2": {
            "subarray_templates": ["*_AA2"],
            "other_config": "..."
        }
    }

Template Processing
-------------------

The template mapping system processes subarray templates through:

1. **Pattern Matching**: Uses fnmatch patterns to find matching templates
2. **Telescope Filtering**: Automatically filters templates based on telescope type (MID/LOW)
3. **Dynamic Loading**: Templates are loaded from JSON files and merged into capabilities
4. **Key Normalization**: Template keys are converted to lowercase for consistency

Template Processing Flag
--------------------------------

``get_osd_using_tmdata`` takes a ``process_templates`` flag, ``False`` by default:

* ``False``: the array assemblies are returned as stored, with their
  ``subarray_templates`` patterns.
* ``True``: each array assembly's ``subarray_templates`` patterns are replaced by
  the templates they match.

The repository's ``get_subarray_templates(telescope, capability_set)`` returns the
matching templates as ``SubarrayTemplate`` models.

Template File Structure
-----------------------

Template files should contain telescope-specific templates:

.. code-block:: json

    {
        "MID_Template_AA0.5": {
            "frequency_band": "1",
            "config": {
                "beam_id": 1,
                "channels": [[0, 1], [744, 8191]]
            }
        },
        "LOW_Template_AA1": {
            "frequency_band": "low1",
            "config": {
                "beam_id": 1,
                "stations": [[0, 1], [2, 3]]
            }
        }
    }

Processed Templates
-------------------

With ``process_templates=True``, the templates are included in the OSD data:

.. code-block:: python

    get_osd_using_tmdata(
        tmdata, telescope=Telescope.MID, cycle_id=1, process_templates=True
    )

* Complete response structure with processed templates:

.. code-block:: json

    {
        "observatory_policy": {
            "cycle_number": 1,
            "telescope_capabilities": {
                "Mid": "AA2",
                "Low": "AA2"
            }
        },
        "capabilities": {
            "mid": {
                "basic_capabilities": {
                    "dish_elevation_limit_deg": 15,
                    "receiver_information": [
                        {
                            "max_frequency_hz": 1050000000,
                            "min_frequency_hz": 350000000,
                            "rx_id": "Band_1"
                        }
                    ]
                },
                "AA2": {
                    "available_receivers": ["Band_1", "Band_2"],
                    "number_ska_dishes": 64,
                    "cbf_modes": ["correlation", "pst", "pss"],
                    "subarray_templates": {
                        "MID_FULL_AA2": {
                            "subarray_type": "AA2",
                            "custom_stations": "",
                            "description": "Full SKA-Mid array, AA2 release."
                        }
                    }
                }
            }
        }
    }
