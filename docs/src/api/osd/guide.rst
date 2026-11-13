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
    │   ├── TEST_SKAO_2027_Low_AA2_SV.json
    │   └── <cycle>.json
    ├── telescopes
    │   ├── ska_low
    │   │   ├── array_assemblies
    │   │   │   └── <array assembly>.json
    │   │   ├── policies
    │   │   │   └── <policy>.json
    │   │   ├── subarray_templates
    │   │   │   └── <array assembly>.json
    │   │   ├── basic_capabilities.json
    │   │   └── defaults.json
    │   └── ska_mid
    │       ├── array_assemblies
    │       │   └── <array assembly>.json
    │       ├── policies
    │       │   └── <policy>.json
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

Each file names what it describes in a field, so file names don't matter:

.. list-table::
   :header-rows: 1

   * - File
     - Identified by
     - Holds
   * - ``basic_capabilities.json``
     - ``telescope``
     - what is fixed for the telescope: Mid's receiver bands
       (``frequency_bands``) or Low's one ``frequency_band``, the
       ``elevation_limits``, and for Low its ``coarse_channels`` and, in
       ``modes``, how each observing mode divides them
   * - ``array_assemblies/*.json``
     - ``array_assembly``
     - what one array assembly offers, such as ``AA2``: its receptors,
       bandwidth, CBF modes and, in ``modes``, each observing mode's beams and
       zoom windows
   * - ``policies/*.json``
     - ``policy``
     - what a cycle holds back of an array assembly: only the fields it
       changes, such as ``AA2_SV``
   * - ``cycles/*.json``
     - ``cycle_id``
     - a cycle: its proposal window and policy, and for each telescope its
       array assembly and the policy offered for each policy type

.. note::

    The legacy ``observatory_policies.json`` file remains at the root on main
    for backward compatibility with the old legacy version mapper.

.. _how-capabilities-are-built:

How capabilities are built
~~~~~~~~~~~~~~~~~~~~~~~~~~~

What a telescope offers, its *capabilities*, is built from three layers, each
changed for its own reason:

.. code-block:: text

    capabilities = basic capabilities           fixed for the telescope
                 + array assembly               a construction milestone
                 with a policy's changes        SciOps' access rules, if a policy applies

Basic capabilities
    What the telescope's design fixes, however much of it is built: Mid's
    receiver bands, Low's frequency band and coarse channels, and the elevation
    limits. They change only if the design does.

Array assemblies
    What has been built at each construction milestone, such as ``AA2``: the
    receptors, bandwidth, CBF modes, and each observing mode's beams and zoom
    windows. They follow the construction rollout; each milestone is its own
    array assembly.

Policies
    The rules Science Operations sets for what can be used of an array assembly
    in a cycle, such as fewer zoom windows and beams during Science
    Verification. A cycle names the policy it offers for each policy type, so
    SciOps can change what is offered without changing what is built.

How the layers combine:

* A policy replaces only the fields it sets; anything it doesn't set comes from
  the array assembly. An empty policy offers the whole array assembly.
* The basic capabilities and the array assembly set different fields, and
  neither an array assembly nor a policy may set a basic field. They can share
  a group: ``modes.spectral`` takes its channels per coarse channel from Low's
  basic capabilities and its zoom windows from the array assembly.
* The result names its ``telescope``, ``array_assembly`` and ``policy``.

A cycle pairs each telescope's array assembly with the policy offered for each
policy type. Low AA2 Science Verification, for example, is the ``AA2`` array
assembly with the ``AA2_SV`` policy, which offers one zoom window, one PST beam
and no PSS beams.

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
cycle_id               the cycle's ``cycle_number``, an integer such as 0, 1, 2; a cycle
                       without a number can't be selected
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
observatory_policy        the cycle file whose ``cycle_number`` is ``cycle_id``, with the legacy field names
telescope_capabilities    the name of what the selected cycle offers on each telescope (its policy), keyed ``Mid`` and ``Low``
capabilities              key value pair of mid and low
Mid                       ``basic_capabilities``, and the capabilities of each array assembly (AA0.5, AA1 etc) and policy a cycle offers, by name, of SKA-Mid
Low                       ``basic_capabilities``, and the capabilities of each array assembly (AA0.5, AA1 etc) and policy a cycle offers, by name, of SKA-Low
======================    ============================================================================================================


Scenarios
~~~~~~~~~~

1. With no filters, it returns the complete OSD catalogue: every telescope's
   ``basic_capabilities`` together with all of its named array assemblies. No
   ``observatory_policy`` is included, since no ``cycle_id`` was selected.

2. With ``cycle_id``, it checks that a file in ``cycles`` has that ``cycle_number``, then selects
   what the cycle offers on each telescope. The cycle file is returned as ``observatory_policy``.

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
                "receptor_ids": [],
                "description": "Full SKA-Low array, AA2 release."
            }
        ]
    }

An array assembly offers the templates in the file of the same name; one with
no template file, such as the ITFs, offers none.

Reading the templates
---------------------

* The repository's ``get_subarray_templates(telescope, array_assembly)`` returns
  an array assembly's templates as a list of ``SubarrayTemplate`` models.
* The PHT views take ``include_subarray_templates``, ``False`` by default. With
  ``True``, the capabilities each telescope offers are served with
  ``subarray_templates``: the templates of the cycle's array assembly keyed by
  name, as the legacy API serves them, or ``{}`` if it has none. With ``False``
  the key is left out.
* The legacy ``get_osd_using_tmdata`` takes ``process_templates``, ``False`` by
  default. With ``False``, the capabilities are returned with the template
  pattern of their array assembly, e.g. ``"subarray_templates": ["*_AA2"]``, as
  before. With ``True``, the pattern is replaced by the array assembly's
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
