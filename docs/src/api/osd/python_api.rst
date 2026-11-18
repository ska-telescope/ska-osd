Python API
-------------------

The OSD is a Python library: its data is read through a *repository* that returns
the data as Pydantic models.

.. contents::


Overview
~~~~~~~~~

* ``OSDRepository`` (``ska_ost_osd.osd.repository``) is the interface for reading
  the OSD: cycles, capabilities, basic capabilities, constraints, defaults and
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
``File`` suffix (e.g. ``MidArrayAssemblyFile``), which validates the file as a whole.
The storage models are part of the TMData adapter
(``ska_ost_osd.osd.adapters.tmdata.models``), not of the API.

Create the TMData client, which chooses the source and version, and a repository
over it. Every call reads through the client, so newly published data is seen
straight away; don't keep results longer than you need them:

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
     - ``Cycle``: a cycle's description, proposal window and policy, and in
       ``telescopes``, a ``CycleTelescope`` for each telescope: its array
       assembly and the policy offered for each policy type
   * - ``get_array_assembly_capabilities(telescope)``
     - each of a telescope's array assemblies, as below
   * - ``get_capabilities(telescope, array_assembly, policy_id=None)``
     - ``MidCapabilities`` / ``LowCapabilities``: everything a telescope
       offers with one array assembly, e.g. ``"AA2"``: its basic capabilities
       and the array assembly's, with a policy's changes applied if one is
       given, e.g. ``"AA2_SV"`` (see :ref:`how capabilities are built
       <how-capabilities-are-built>` in the guide). It names its
       ``telescope``, ``array_assembly`` and ``policy`` (``None`` without
       one). Each observing mode's channels, zoom windows and beams are in
       ``observing_modes``, its stations (Low) or dishes (Mid) in ``receptors``,
       its frequency slice processors, function modes and (Mid) channel limit
       in ``cbf``, and Low's coarse channels and subarray beams in ``sps``.
       Mid's ``allowed_channel_width_values_hz`` lists the channel widths its
       zoom and channel averaging factors give. Its ``cbf.max_channels`` is
       ``None`` when the OSD sets no channel limit
   * - ``get_basic_capabilities(telescope)``
     - ``MidBasicCapabilities`` / ``LowBasicCapabilities``: what is fixed for
       the telescope, whatever the array assembly. For Mid, its receiver
       bands as ``frequency_bands``, its ``elevation_limits``, and in ``cbf``
       the ``frequency_slice_bandwidth_hz`` each FSP processes and the
       ``fine_channel_width_hz`` it divides a slice into; for Low, its
       one ``frequency_band``, its ``elevation_limits``, its
       ``sps.coarse_channels`` and, in ``observing_modes``, how each observing mode
       divides a coarse channel
   * - ``get_constraints(telescope)``
     - ``Constraints``: the elevation limits and the sun, moon and Jupiter
       avoidance angles
   * - ``get_defaults(telescope)``
     - ``MidDefaults`` (the SPFRx defaults) / ``LowDefaults`` (the quality
       attribute metrics)

For Low AA2 with the ``AA2_SV`` policy, and Mid AA2 with no policy:

.. code-block:: python

    from ska_ost_osd.osd.common.constant import Telescope

    low = repository.get_capabilities(Telescope.SKA_LOW, "AA2", "AA2_SV")
    mid = repository.get_capabilities(Telescope.SKA_MID, "AA2")
    repository.get_constraints(Telescope.SKA_MID).min_elevation_deg  # 15.0

Mid's receiver bands are looked up on its basic capabilities:

.. code-block:: python

    bands = repository.get_basic_capabilities(Telescope.SKA_MID)
    bands.get_frequency_band("Band_2").max_frequency_hz
    bands.get_frequency_band("Band_5b").get_band5b_subband(2).lo_frequency_hz

.. _example-low-aa2-sv:

Example: Low AA2 with the AA2_SV policy
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``low`` above, as JSON, with long lists shortened:

.. code-block:: json

    {
      "telescope": "ska_low",
      "array_assembly": "AA2",
      "policy": "AA2_SV",
      "frequency_band": {
        "max_frequency_hz": 350000000.0,
        "min_frequency_hz": 50000000.0
      },
      "elevation_limits": {
        "min_elevation_deg": 45.0,
        "max_elevation_deg": 90.0
      },
      "sps": {
        "coarse_channels": {
          "min": 64,
          "max": 447,
          "width_hz": 781250.0
        },
        "subarray_beams": {
          "max_subarray_beams": 1,
          "max_substations_per_subarray_beam": 0
        }
      },
      "available_bandwidth_hz": 150000000.0,
      "cbf": {
        "number_fsps": 10,
        "function_modes": ["vis", "pst"]
      },
      "observing_modes": {
        "continuum": {
          "channels_per_coarse_channel": 144
        },
        "spectral": {
          "channels_per_coarse_channel": 432,
          "max_zoom_windows": 1,
          "max_zoom_channels": 4000,
          "zoom_factors": [1, 2, 3]
        },
        "pss": {
          "channels_per_coarse_channel": 54,
          "max_beams": 0,
          "beam_bandwidth_hz": 118000000.0
        },
        "pst": {
          "channels_per_coarse_channel": 216,
          "max_beams": 1
        },
        "vlbi": {
          "max_beams": 0
        }
      },
      "receptors": {
        "number_stations": 68,
        "max_baseline_km": 40.0,
        "receptor_ids": [315, 316, 317, "..."]
      }
    }

.. _example-mid-aa2:

Example: Mid AA2
^^^^^^^^^^^^^^^^^

``mid`` above, as JSON, with long lists shortened. Its
``allowed_channel_width_values_hz`` is worked out from the zoom and averaging
factors, not stored:

.. code-block:: json

    {
      "telescope": "ska_mid",
      "array_assembly": "AA2",
      "policy": null,
      "frequency_bands": [
        {
          "max_frequency_hz": 1050000000.0,
          "min_frequency_hz": 350000000.0,
          "rx_id": "Band_1",
          "band5b_subbands": null
        },
        "..."
      ],
      "elevation_limits": {
        "min_elevation_deg": 15.0,
        "max_elevation_deg": 85.0
      },
      "cbf": {
        "frequency_slice_bandwidth_hz": 198180864,
        "fine_channel_width_hz": 13440,
        "number_fsps": 26,
        "function_modes": ["correlation", "pst", "pss"],
        "max_channels": null
      },
      "available_bandwidth_hz": 800000000.0,
      "observing_modes": {
        "continuum": {
          "channel_averaging_factors": [1, 2, 3, 4, 6, 8, 12, 16, 24, 31, 32, 48]
        },
        "spectral": {
          "max_zoom_windows": 16,
          "max_zoom_channels": 14880,
          "zoom_factors": [1, 2, 3, 4, 5, 6]
        },
        "pss": {
          "max_beams": 384,
          "beam_bandwidth_hz": 800000000.0
        },
        "pst": {
          "max_beams": 6
        }
      },
      "receivers": ["Band_1", "Band_2", "Band_5a", "Band_5b"],
      "receptors": {
        "number_ska_dishes": 64,
        "number_meerkat_dishes": 4,
        "number_meerkatplus_dishes": 0,
        "max_baseline_km": 110.0,
        "receptor_ids": ["SKA001", "SKA008", "SKA013", "..."]
      },
      "allowed_channel_width_values_hz": [210, 420, 840, "..."]
    }


Joins
~~~~~~

.. list-table::
   :header-rows: 1

   * - Method
     - Returns
   * - ``get_cycle_capabilities(cycle_id)``
     - the capabilities the cycle offers for each telescope and policy type,
       as a ``dict`` keyed by ``Telescope`` and then ``PolicyType``: the
       cycle's array assembly for that telescope with the type's policy
       applied. A telescope the cycle does not offer is left out
   * - ``get_subarray_templates(telescope, array_assembly)``
     - the ``SubarrayTemplate`` objects an array assembly offers, or none


Views
~~~~~~

The views in ``ska_ost_osd.osd.views`` build what ska-oso-services serves to its
UIs, as Pydantic models. Each consumer's views and models are in its own module:
``views.odt`` for the ODT and ``views.pht`` for the PHT. Each view takes an
``OSDRepository``, so it works with any repository.

.. list-table::
   :header-rows: 1

   * - View
     - Returns
     - Served by ska-oso-services
     - Used by
   * - ``odt.get_basic_capabilities(repository, telescope)``
     - Mid: ``list[MidFrequencyBand]``; Low: ``LowFrequencyBand``
     - ``frequency_band`` in ``GET /configuration``
     - ODT UI
   * - ``odt.get_constraints(repository, telescope)``
     - ``Constraints``
     - ``constraints`` in ``GET /configuration``
     - ODT UI
   * - ``odt.get_defaults(repository, telescope)``
     - Mid: ``SPFRxParameters``; Low: ``LowQualityAttributeMetrics``
     - ``spfrx_defaults`` and ``quality_attribute_metrics`` in
       ``GET /configuration``
     - ODT UI
   * - ``odt.get_capabilities(repository, telescope, array_assembly,
       policy_id=None)``
     - Mid: ``MidSubarray``; Low: ``LowSubarray``
     - each of the ``subarrays`` in ``GET /configuration``
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

ska-oso-services builds ``GET /configuration`` from the ODT view's functions,
choosing which array assemblies and policies to serve:

.. code-block:: text

    ska_mid
        frequency_band              get_basic_capabilities: the receiver bands,
                                    Band 5b with its sub-bands
        constraints                 get_constraints: elevation limits and
                                    avoidance angles
        subarrays                   get_capabilities, for each array assembly
                                    or policy
        spfrx_defaults              get_defaults: target_spfrx and csp_spfrx
    ska_low
        frequency_band              get_basic_capabilities: the band and its
                                    channels
        constraints                 get_constraints
        quality_attribute_metrics   get_defaults
        subarrays                   get_capabilities, for each array assembly
                                    or policy

``get_capabilities`` returns an array assembly's capabilities, with a policy's
applied if one is given, named after the policy or else the array assembly. Its
fields are the ones the ODT uses: ``name``, ``receptors``,
``available_bandwidth_hz``, ``number_pst_beams`` and ``number_fsps``, with Mid's
``allowed_channel_width_values_hz`` and Low's ``number_substations`` and
``number_subarray_beams``. Use ``repository.get_capabilities`` for all of their
capabilities.

.. code-block:: python

    from ska_ost_osd.osd.views import odt

    odt.get_capabilities(repository, Telescope.SKA_LOW, "AA2", "AA2_SV")

The models are the view's own, named and shaped as ska-oso-services' response
models, so the response doesn't change with the OSD's domain models.


PHT cycle data
^^^^^^^^^^^^^^^

``get_cycle_configuration(repository, cycle_id)`` returns one cycle with what it
offers; ``get_cycle_configurations(repository)`` returns every cycle:

.. code-block:: text

    observatory_policy          the cycle: cycle_number, cycle_id, type,
                                cycle_description, cycle_information (the
                                cycle ID and proposal dates), cycle_policies
                                (the proposal policy), telescope_capabilities
    capabilities
        mid                     null if the cycle doesn't offer Mid
            basic_capabilities  receiver_information: the receiver bands
            "AA2"               the capabilities offered, keyed by the
                                policy's name
        low                     null if the cycle doesn't offer Low
            basic_capabilities  min_frequency_hz and max_frequency_hz
            "AA2"               the capabilities offered, keyed by the
                                policy's name

The PHT UI reads the field names of the response it already uses, and the views
serialise with those names by default, without ``by_alias=True``:
``telescope_capabilities`` as ``Mid`` and ``Low``, Mid's receiver bands as
``receiver_information``, and Mid's channel widths also as
``allowed_channel_width_values``. The PHT UI finds the capabilities as the first
key under ``mid`` or ``low`` that isn't ``basic_capabilities``.

.. code-block:: python

    from ska_ost_osd.osd.views.pht import get_cycle_configuration

    get_cycle_configuration(repository, "TEST_SKAO_2027_Low_AA2_SV").model_dump(
        mode="json"
    )


Errors
~~~~~~~

A key with no data raises a subclass of ``OSDQueryError``
(``ska_ost_osd.osd.exceptions``), which is also a ``LookupError``: for example
``CycleNotFoundError``, ``ArrayAssemblyNotFoundError`` or ``PolicyNotFoundError``.
``TMDataRepository`` raises ``FileNotFoundError`` if a tmdata file is missing, and
``ValueError`` if two files claim the same cycle, array assembly or policy.
