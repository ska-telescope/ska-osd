Python API
-------------------

The OSD is a Python library: its data is read through a *repository* that returns
the data as Pydantic models.

.. contents::


Overview
~~~~~~~~~

* ``OSDRepository`` (``ska_ost_osd.osd.repository``) is the interface for reading
  the OSD: cycles, capability sets, basic capabilities, constraints, defaults and
  subarray templates, and the links between them. A method named in the plural
  returns all of something; one named in the singular looks one item up by its key
  and raises an error if there is none.
* ``TMDataRepository`` (``ska_ost_osd.osd.adapters.tmdata``) implements it by
  reading the tmdata through a TMData client.
* **Views** take any ``OSDRepository`` and combine its data into the shapes
  ska-oso-services serves, one module per consumer: the ODT configuration in
  ``ska_ost_osd.osd.views.odt`` and the PHT cycle data in
  ``ska_ost_osd.osd.views.pht``.

The repository returns *reader models*, the data as callers use it. The
``TMDataRepository`` reads each tmdata file through a *storage model*, named with a
``File`` suffix (e.g. ``MidCapabilitySetFile``), which validates the file as a whole.
The storage models are part of the TMData adapter
(``ska_ost_osd.osd.adapters.tmdata.models``), not of the API.

Create the TMData client, which chooses the source and version, and a repository
over it once; cache the results if needed:

.. code-block:: python

    from ska_telmodel_client import TMData

    from ska_ost_osd.osd.adapters.tmdata import TMDataRepository

    repository = TMDataRepository(TMData(["car:ost/ska-ost-osd?main"], update=True))


Reading the data
~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Method
     - Returns
   * - ``get_cycle_ids()``
     - the cycle IDs, in ascending order
   * - ``get_cycles()`` / ``get_cycle(cycle_id)``
     - ``Cycle``: a cycle's description, proposal window and policy, and for
       each telescope its array assembly and the capability set offered for
       each policy type
   * - ``get_capability_sets(telescope)``
     - each of a telescope's array assemblies, as below
   * - ``get_capability_set(telescope, array_assembly, policy_id=None)``
     - ``MidCapabilitySet`` / ``LowCapabilitySet``: one array assembly of a
       telescope, e.g. ``"AA2"``, with a policy's changes applied if one is
       given, e.g. ``"AA2_SV"``. Its zoom windows and beams are in its
       ``modes``, its receptors in ``stations`` (Low) or ``dishes`` (Mid), and
       Low's subarray beams in ``subarray_beams``
   * - ``get_basic_capabilities(telescope)``
     - ``MidBasicCapabilities`` / ``LowBasicCapabilities``: what is fixed for
       the telescope, whatever the array assembly. For Mid, its receiver
       bands as ``frequency_bands`` and its ``elevation_limits``; for Low, its
       one ``frequency_band``, its ``elevation_limits``, its
       ``coarse_channels`` and, in ``modes``, how each observing mode divides
       a coarse channel
   * - ``get_constraints(telescope)``
     - ``Constraints``: the elevation limits and the sun, moon and Jupiter
       avoidance angles
   * - ``get_defaults(telescope)``
     - ``MidDefaults`` (the SPFRx defaults) / ``LowDefaults`` (the quality
       attribute metrics)

.. code-block:: python

    from ska_ost_osd.osd.common.constant import Telescope

    aa2 = repository.get_capability_set(Telescope.SKA_LOW, "AA2")
    aa2.subarray_beams.max_subarray_beams                        # 8
    repository.get_constraints(Telescope.SKA_MID).min_elevation_deg  # 15.0

Mid's receiver bands are looked up on its basic capabilities:

.. code-block:: python

    bands = repository.get_basic_capabilities(Telescope.SKA_MID)
    bands.get_frequency_band("Band_2").max_frequency_hz
    bands.get_frequency_band("Band_5b").get_band5b_subband(2).lo_frequency_hz


Joins
~~~~~~

.. list-table::
   :header-rows: 1

   * - Method
     - Returns
   * - ``get_cycle_capability_sets(cycle_id)``
     - the capabilities the cycle offers for each telescope and policy type,
       as a ``dict`` keyed by ``Telescope`` and then ``PolicyType``: the
       cycle's array assembly for that telescope with the type's policy
       applied. A telescope the cycle does not offer is left out
   * - ``get_subarray_templates(telescope, capability_set)``
     - the ``SubarrayTemplate`` objects of a capability set: the templates of
       the array assembly the capability set names, or none


Views
~~~~~~

The views in ``ska_ost_osd.osd.views`` build the responses ska-oso-services serves
to its UIs. Each consumer's views and response models are in its own module:
``views.odt`` for the ODT and ``views.pht`` for the PHT. Each takes an ``OSDRepository``, so it works with any repository, and
returns a Pydantic model that ska-oso-services can use directly as the FastAPI
response model of the endpoint.

.. list-table::
   :header-rows: 1

   * - View
     - Returns
     - Served by ska-oso-services
     - Used by
   * - ``odt.get_configuration(repository)``
     - ``Configuration``
     - ``GET /configuration``
     - ODT UI
   * - ``pht.get_cycle_configuration(repository, cycle_id)``
     - ``CycleConfiguration``
     - ``GET /prsls/osd/{cycle}``
     - PHT UI
   * - ``pht.get_cycle_configurations(repository)``
     - ``list[CycleConfiguration]``, in ascending order of cycle ID
     - ``GET /prsls/osd/cycles``
     - PHT UI


ODT configuration
^^^^^^^^^^^^^^^^^^

``get_configuration(repository)`` returns everything the ODT needs about both
telescopes, independent of any cycle:

.. code-block:: text

    ska_mid
        frequency_band          the receiver bands, Band 5b with its sub-bands
        constraints             elevation limits and avoidance angles
        subarrays               each capability set: name, receptors,
                                available_bandwidth_hz, number_pst_beams,
                                number_fsps, allowed_channel_width_values_hz
        spfrx_defaults          target_spfrx and csp_spfrx
    ska_low
        frequency_band          the band and its channels
        constraints             elevation limits and avoidance angles
        quality_attribute_metrics
        subarrays               each capability set: name, receptors,
                                available_bandwidth_hz, number_pst_beams,
                                number_fsps, number_substations,
                                number_subarray_beams

The capability sets are narrowed to the fields the ODT uses; use
``repository.get_capability_set`` for all of a capability set's fields. The JSON
matches what ska-oso-services serves today, with one addition:
``allowed_channel_width_values_hz`` on the Mid capability sets, which
ska-oso-services means to serve but currently drops.


PHT cycle data
^^^^^^^^^^^^^^^

``get_cycle_configuration(repository, cycle_id)`` returns one cycle with what it
offers; ``get_cycle_configurations(repository)`` returns every cycle. Both take
``include_subarray_templates``, ``False`` by default, to serve each offered
capability set's subarray templates as the legacy API does with
``process_templates=True``:

.. code-block:: text

    observatory_policy          the cycle: cycle_number, cycle_id, type,
                                cycle_description, cycle_information (the
                                cycle ID and proposal dates), cycle_policies
                                (the proposal policy), telescope_capabilities
    capabilities
        mid                     null if the cycle doesn't offer Mid
            basic_capabilities  receiver_information: the receiver bands
            "AA2"               the offered capability set, keyed by its name;
                                with include_subarray_templates, its
                                subarray_templates keyed by template name
        low                     null if the cycle doesn't offer Low
            basic_capabilities  the band and its channels
            "AA2"               the offered capability set, keyed by its name

The PHT UI reads the field names of the response it already uses, and the views
serialise with those names by default, without ``by_alias=True``:
``telescope_capabilities`` as ``Mid`` and ``Low``, Mid's receiver bands as
``receiver_information``, and Mid's channel widths also as
``allowed_channel_width_values``. The PHT UI finds the capability set as the first key
under ``mid`` or ``low`` that isn't ``basic_capabilities``.

.. code-block:: python

    from ska_ost_osd.osd.views.pht import get_cycle_configuration

    get_cycle_configuration(repository, "SKAO_2027_1").model_dump(mode="json")


Errors
~~~~~~~

A key with no data raises a subclass of ``OSDQueryError``
(``ska_ost_osd.osd.exceptions``), which is also a ``LookupError``: for example
``CycleNotFoundError`` or ``CapabilitySetNotFoundError``. ``TMDataRepository``
raises ``FileNotFoundError`` if a tmdata file is missing.
