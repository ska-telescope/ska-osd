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
    ├── telescopes
    │   ├── ska_low
    │   │   ├── capabilities
    │   │   │   └── <capability set>.json
    │   │   ├── subarray_templates
    │   │   │   └── <array assembly>.json
    │   │   ├── basic_capabilities.json
    │   │   └── defaults.json
    │   └── ska_mid
    │       ├── capabilities
    │       │   └── <capability set>.json
    │       ├── subarray_templates
    │       │   └── <array assembly>.json
    │       ├── basic_capabilities.json
    │       └── defaults.json
    ├── ska1_low                             (legacy)
    │   ├── low_capabilities.json
    │   └── low_defaults.json
    ├── ska1_mid                             (legacy)
    │   ├── mid_capabilities.json
    │   └── mid_defaults.json
    ├── subarray_templates                   (legacy)
    │   └── subarray_template_library.json
    └── observatory_policies.json            (legacy)

The current files are in ``cycles`` and ``telescopes``. The legacy files are
kept for older releases of the OSD and for consumers that read them directly;
the current code does not read them.


* `mid_capabilities.json <https://confluence.skatelescope.org/pages/viewpage.action?spaceKey=SWSI&title=Observatory+Static+Data>`_

* `low_capabilities.json <https://confluence.skatelescope.org/pages/viewpage.action?spaceKey=SWSI&title=Observatory+Static+Data>`_

Each telescope's basic capabilities are in its ``basic_capabilities.json``
file: its ``frequency_bands`` (Mid's receiver bands; Low's one band, with its
coarse channels) and its ``elevation_limits``. Each of
its capability sets is in its own file in ``capabilities``, named after the
capability set, such as ``capabilities/AA2.json``.

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

    tmdata = TMData(["car:ost/ska-ost-osd?<version>"], update=True)
    osd_data = get_osd_using_tmdata(tmdata, telescope=Telescope.SKA_LOW, cycle_id=1)

===================    ============================================================
Parameters             Description
===================    ============================================================
tm_data                the TMData client to read the tmdata from
cycle_id               Cycle Id a integer value 1, 2, 3
telescope              ``Telescope.SKA_MID`` or ``Telescope.SKA_LOW``; ``"mid"``
                       and ``"low"`` are still accepted
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
        "telescope_capabilities": {"Low": "AA2"}
      },
      "capabilities": {
        "low": {"basic_capabilities": {}, "AA2": {}}
      }
    }


======================    ============================================================================================================
Keys                      Description
======================    ============================================================================================================
observatory_policy        file content of the selected ``cycles/cycle_<id>.json`` file
telescope_capabilities    value of ``telescope_capabilities`` in the selected cycle file, keyed ``Mid`` and ``Low``
capabilities              key value pair of mid and low
Mid                       ``basic_capabilities`` and the capability sets (``Array Assembly`` AA0.5, AA1 etc) of SKA-Mid
Low                       ``basic_capabilities`` and the capability sets (``Array Assembly`` AA0.5, AA1 etc) of SKA-Low
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

      Array assembly AA1 does not match capability low in cycle 2. Expected AA2.

* a ``cycle_id``, ``telescope`` or ``array_assembly`` with no data, or a telescope
  that the cycle doesn't offer.


Publishing tmdata
~~~~~~~~~~~~~~~~~~

The tmdata is published to CAR with the same version as the Python package, so a
breaking change to the tmdata is released as a new major version. Consumers should
read a pinned version, ``car:ost/ska-ost-osd?<version>`` (e.g. ``?8.0.0``), rather
than ``main``.

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

A subarray template is a named set of receptors from an array assembly. Each
telescope's templates are stored by array assembly, in
``telescopes/<telescope>/subarray_templates/<array assembly>.json``, as a list:

.. code-block:: json

    {
        "templates": [
            {
                "name": "SKA_LOW_FULL_AA2",
                "subarray_type": "AA2",
                "custom_stations": [],
                "description": "Full SKA-Low array, AA2 release."
            }
        ]
    }

A capability set offers the templates of the array assembly it names in its
``array_assembly`` field:

.. code-block:: json

    {
        "number_stations": 68,
        "array_assembly": "AA2"
    }

A capability set with no ``array_assembly`` (the ITFs), or whose array assembly
has no template file, offers no templates.

Reading the templates
---------------------

* The repository's ``get_subarray_templates(telescope, capability_set)`` returns
  a capability set's templates as a list of ``SubarrayTemplate`` models.
* The PHT views take ``include_subarray_templates``, ``False`` by default. With
  ``True``, each offered capability set is served with ``subarray_templates``: its
  templates keyed by name, as the legacy API serves them, or ``{}`` if it has
  none. With ``False`` the key is left out.
* The legacy ``get_osd_using_tmdata`` takes ``process_templates``, ``False`` by
  default. With ``False``, each capability set is returned with the template
  pattern of its array assembly, e.g. ``"subarray_templates": ["*_AA2"]``, as
  before. With ``True``, the pattern is replaced by its array assembly's
  templates, as below.

Processed Templates
-------------------

With ``process_templates=True``, the templates are included in the OSD data:

.. code-block:: python

    get_osd_using_tmdata(
        tmdata, telescope=Telescope.SKA_LOW, cycle_id=1, process_templates=True
    )

* Complete response structure with processed templates:

.. code-block:: json

    {
        "observatory_policy": {
            "cycle_number": 1,
            "telescope_capabilities": {
                "Low": "AA2"
            }
        },
        "capabilities": {
            "low": {
                "basic_capabilities": {
                    "min_frequency_hz": 50000000.0,
                    "max_frequency_hz": 350000000.0
                },
                "AA2": {
                    "number_stations": 68,
                    "cbf_modes": ["vis", "pst"],
                    "subarray_templates": {
                        "SKA_LOW_FULL_AA2": {
                            "subarray_type": "AA2",
                            "custom_stations": "",
                            "description": "Full SKA-Low array, AA2 release."
                        }
                    }
                }
            }
        }
    }
