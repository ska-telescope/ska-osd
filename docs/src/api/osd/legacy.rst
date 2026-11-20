Legacy
------

.. deprecated:: 8.0.0
    ``ska_ost_osd.osd.osd``, including ``get_osd_using_tmdata``, will be removed
    in a future release. Read the OSD through the repository and the views
    described in :doc:`python_api`; :doc:`migration` maps the legacy fields to
    their new models.

.. contents::


Querying the OSD
~~~~~~~~~~~~~~~~

``get_osd_using_tmdata`` (``ska_ost_osd.osd.osd``) returns the OSD data as a
dictionary, selected by cycle, telescope and array assembly.

.. code-block:: python

    from ska_telmodel_client import TMData

    from ska_ost_osd.osd.common.constant import Telescope
    from ska_ost_osd.osd.osd import get_osd_using_tmdata

    tmdata = TMData(["car:ost/ska-ost-osd?<version>"], update=True)
    osd_data = get_osd_using_tmdata(tmdata, telescope=Telescope.SKA_LOW, cycle_id=2)

===================    ============================================================
Parameters             Description
===================    ============================================================
tm_data                the TMData client to read the tmdata from
cycle_id               the cycle's ``cycle_number``, an integer such as 0, 1, 2; a cycle
                       without a number can't be selected
telescope              ``Telescope.SKA_MID`` or ``Telescope.SKA_LOW``; ``"mid"``
                       and ``"low"`` are still accepted
array_assembly         the name of an array assembly, e.g. ``AA2``, or of a policy
                       a cycle offers, e.g. ``AA2_SV``; with ``cycle_id``, the
                       name the cycle offers on the telescope
process_templates      whether to replace the ``subarray_templates`` patterns with
                       the templates, see `Subarray Template Support`_
===================    ============================================================

Response
~~~~~~~~

.. code-block:: json

    {
      "observatory_policy": {
        "cycle_number": 2,
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
~~~~~~~~~

1. With no filters, it returns the complete OSD catalogue: every telescope's
   ``basic_capabilities`` together with all of its array assemblies and the
   policies the cycles offer, by name. No ``observatory_policy`` is included,
   since no ``cycle_id`` was selected.

2. With ``cycle_id``, it checks that a file in ``cycles`` has that ``cycle_number``, then selects
   what the cycle offers on each telescope. The cycle file is returned as ``observatory_policy``.

3. With ``telescope``, it returns only that telescope; with ``array_assembly`` as
   well, only the array assembly or policy of that name.


Error Handling
``````````````

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

Subarray Template Support
~~~~~~~~~~~~~~~~~~~~~~~~~

The legacy ``get_osd_using_tmdata`` takes ``process_templates``, ``False`` by
default. With ``False``, the capabilities are returned with the template
pattern of their array assembly, e.g. ``"subarray_templates": ["*_AA2"]``, as
before. With ``True``, the pattern is replaced by the array assembly's
templates, as below.

Processed Templates
```````````````````

With ``process_templates=True``, the templates are included in the OSD data:

.. code-block:: python

    get_osd_using_tmdata(
        tmdata, telescope=Telescope.SKA_LOW, cycle_id=2, process_templates=True
    )

* Complete response structure with processed templates:

.. code-block:: json

    {
        "observatory_policy": {
            "cycle_number": 2,
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

.. _legacy-publishing:

Publishing before 8.0.0
~~~~~~~~~~~~~~~~~~~~~~~

Before 8.0.0, the tmdata was published with releases of ska-ost-osd, under the
release's tag, e.g. ``car:ost/ska-ost-osd?7.0.0``. Two files on ``main`` told
clients which release to read:

* `tmdata/version_mapping/latest_release.txt <https://gitlab.com/ska-telescope/ost/ska-ost-osd/-/blob/main/tmdata/version_mapping/latest_release.txt?ref_type=heads>`_:
  the latest release, read by ``get_osd_latest_version``.
* ``tmdata/version_mapping/cycle_gitlab_release_version_mapping.json``: the
  releases holding each cycle's data.

Clients before 8.0.0 still read them, so they stay on ``main``, pointing at 7.0.0
and earlier.

Manual tmdata Release Steps
```````````````````````````

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
