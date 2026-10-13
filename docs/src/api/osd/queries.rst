Python API
-------------------

Besides the REST API, the OSD can be used as a Python library. Functions read the
tmdata through a TMData client the caller creates, and return the data as Pydantic
models.

.. contents::


Overview
~~~~~~~~~

The data is treated as a set of tables, read through three layers of functions:

* **Queries** in ``ska_ost_osd.osd.queries`` read one kind of data: cycles,
  capability sets, basic capabilities, constraints and defaults. A function named
  in the plural returns all of them; one named in the singular looks one up by its
  key and raises an error if there is none.
* **Joins**, also in ``ska_ost_osd.osd.queries``, follow the links between them: the
  capability sets a cycle offers, and the subarray templates of a capability set.
* **Views** in ``ska_ost_osd.osd.views`` combine queries into the shapes
  ska-oso-services serves: the ODT configuration and the PHT cycle data.

The functions return *reader models*, the data as callers use it. Each tmdata file
also has a *storage model*, named with a ``File`` suffix (e.g.
``MidCapabilitiesFile``), which validates the file as a whole; the queries read
the files through these.

Every function takes the TMData client to read from, so the caller chooses the
source and version, and caches the results if needed:

.. code-block:: python

    from ska_telmodel_client import TMData

    tmdata = TMData(["car:ost/ska-ost-osd?main"], update=True)


Queries
~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Function
     - Returns
   * - ``get_cycle_ids(tmdata)``
     - the cycle IDs, in ascending order
   * - ``get_cycles(tmdata)`` / ``get_cycle(tmdata, cycle_id)``
     - ``Cycle``: a cycle's description, proposal dates, policies and the
       capability set each telescope offers
   * - ``get_capability_sets(tmdata, telescope)`` /
       ``get_capability_set(tmdata, telescope, name)``
     - ``MidCapabilitySet`` / ``LowCapabilitySet``: one array assembly of a
       telescope, e.g. ``"AA2"``
   * - ``get_basic_capabilities(tmdata, telescope)``
     - ``MidBasicCapabilities`` (the receiver bands) / ``LowBasicCapabilities``
       (the frequency band and its channels)
   * - ``get_constraints(tmdata, telescope)``
     - ``Constraints``: the elevation limits and the sun, moon and Jupiter
       avoidance angles
   * - ``get_defaults(tmdata, telescope)``
     - ``MidDefaults`` (the SPFRx defaults) / ``LowDefaults`` (the quality
       attribute metrics)

.. code-block:: python

    from ska_ost_osd.osd.common.constant import Telescope
    from ska_ost_osd.osd.queries import get_capability_set, get_constraints

    aa2 = get_capability_set(tmdata, Telescope.LOW, "AA2")
    aa2.number_subarray_beams                                  # 8
    get_constraints(tmdata, Telescope.MID).min_elevation_deg   # 15.0

Mid's receiver bands are looked up on its basic capabilities:

.. code-block:: python

    from ska_ost_osd.osd.queries import get_basic_capabilities

    bands = get_basic_capabilities(tmdata, Telescope.MID)
    bands.get_frequency_band("Band_2").max_frequency_hz
    bands.get_frequency_band("Band_5b").get_band5b_subband(2).lo_frequency_hz


Joins
~~~~~~

.. list-table::
   :header-rows: 1

   * - Function
     - Returns
   * - ``get_cycle_capability_sets(tmdata, cycle_id)``
     - the capability set the cycle offers for each telescope, as a ``dict`` keyed
       by ``Telescope``; a telescope the cycle does not offer is left out
   * - ``get_subarray_templates(tmdata, telescope, capability_set)``
     - the ``SubarrayTemplate`` objects of a capability set: those whose name
       matches one of its ``subarray_templates`` patterns and starts with the
       telescope, e.g. ``MID_``


Views
~~~~~~

.. list-table::
   :header-rows: 1

   * - Function
     - Returns
   * - ``get_configuration(tmdata)``
     - ``Configuration``: both telescopes' bands, constraints, defaults and
       capability sets, as ska-oso-services serves them to the ODT from
       ``GET /configuration``
   * - ``get_cycle_configurations(tmdata)`` /
       ``get_cycle_configuration(tmdata, cycle_id)``
     - ``CycleConfiguration``: a cycle with, for each telescope it offers, the
       offered capability set and that telescope's basic capabilities, as
       ska-oso-services serves them to the PHT from ``GET /prsls/osd/cycles`` and
       ``GET /prsls/osd/{cycle}``

Serialise the cycle views with aliases, as FastAPI does by default, for the field
names the PHT reads (``telescope_capabilities`` as ``Mid`` and ``Low``, Mid's
receiver bands as ``receiver_information``, and each capability set keyed by its
name):

.. code-block:: python

    from ska_ost_osd.osd.views import get_cycle_configuration

    get_cycle_configuration(tmdata, 1).model_dump(mode="json", by_alias=True)


Errors
~~~~~~~

A key with no data raises a subclass of ``OSDQueryError``
(``ska_ost_osd.osd.exceptions``), which is also a ``LookupError``: for example
``CycleNotFoundError`` or ``CapabilitySetNotFoundError``. A missing tmdata file
raises ``FileNotFoundError``.
