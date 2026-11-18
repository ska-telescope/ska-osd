Migrating to version 8.0
-------------------------

``get_osd_using_tmdata`` and the views serve each telescope's capabilities in
the pre-8.0 legacy shape: ``basic_capabilities`` alongside one entry per array
assembly or policy, each with flat field names. In version 8.0 the new Python
API returns them merged into one model, ``MidCapabilities`` or
``LowCapabilities``, with related fields in groups. See the examples in
:doc:`python_api`:

* :ref:`Low AA2 SV <example-low-aa2-sv>`
* :ref:`Mid AA2 <example-mid-aa2>`

The tables below map each legacy field to its place in that model, ignoring the
``basic_capabilities`` or array assembly key it was under. A field is *renamed*
if its path differs, and *changed* if its value is represented differently.
``get_osd_using_tmdata`` and the views still serve the legacy fields.

.. contents::
   :local:


Basic capabilities
~~~~~~~~~~~~~~~~~~~

The fields under ``basic_capabilities``. In the Python API they are part of
every ``MidCapabilities`` or ``LowCapabilities``, and
``repository.get_basic_capabilities(telescope)`` returns them alone.

.. list-table::
   :header-rows: 1
   :widths: 30 10 30 30

   * - Legacy field
     - Telescope
     - Python API
     - Change
   * - ``min_frequency_hz``, ``max_frequency_hz``
     - Low
     - ``frequency_band.min_frequency_hz``, ``frequency_band.max_frequency_hz``
     - Renamed
   * - ``min_coarse_channel``, ``max_coarse_channel``
     - Low
     - ``sps.coarse_channels.min``, ``sps.coarse_channels.max``
     - Renamed. The lowest and highest coarse channel numbers
   * - ``coarse_channel_width_hz``
     - Low
     - ``sps.coarse_channels.width_hz``
     - Renamed
   * - ``coarse_channel_width``
     - Low
     - none
     - Removed: a backwards compatible alias of ``coarse_channel_width_hz``
       that is no longer supported
   * - ``number_continuum_channels_per_coarse_channel``
     - Low
     - ``observing_modes.continuum.channels_per_coarse_channel``
     - Renamed
   * - ``number_zoom_channels_per_coarse_channel``
     - Low
     - ``observing_modes.spectral.channels_per_coarse_channel``
     - Renamed
   * - ``number_pst_channels_per_coarse_channel``
     - Low
     - ``observing_modes.pst.channels_per_coarse_channel``
     - Renamed
   * - ``number_pss_channels_per_coarse_channel``
     - Low
     - ``observing_modes.pss.channels_per_coarse_channel``
     - Renamed
   * - ``receiver_information``
     - Mid
     - ``frequency_bands``
     - Renamed. The ODT view calls it ``frequency_band``. Band 5b's
       ``sub_bands`` are renamed ``band5b_subbands``, as the ODT view serves
       them
   * - none
     - Both
     - ``elevation_limits.min_elevation_deg``,
       ``elevation_limits.max_elevation_deg``
     - Moved from the capabilities files' ``constraints``, see below
   * - none
     - Both
     - ``telescope``
     - Added: ``Telescope.SKA_MID`` or ``Telescope.SKA_LOW``
   * - none
     - Mid
     - ``cbf.frequency_slice_bandwidth_hz``, ``cbf.fine_channel_width_hz``
     - Added: the bandwidth of each frequency slice, and the width of the
       fine channels the FSPs divide it into


Array assembly capabilities
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The fields under each array assembly or policy, e.g. ``"AA2"``. The views serve
some under different names, as given.

.. list-table::
   :header-rows: 1
   :widths: 30 10 30 30

   * - Legacy field
     - Telescope
     - Python API
     - Change
   * - The key, e.g. ``"AA2"`` or ``"AA2_SV"``
     - Both
     - ``array_assembly`` and ``policy``
     - Changed: named by fields; ``policy`` is ``None`` without one. The ODT
       view serves it as a ``name`` field, and the PHT view's
       ``telescope_capabilities`` names it: the policy's name, or else the
       array assembly's
   * - ``available_bandwidth_hz``
     - Both
     - ``available_bandwidth_hz``
     - Unchanged
   * - ``number_fsps``
     - Both
     - ``cbf.number_fsps``
     - Renamed
   * - ``cbf_modes``
     - Both
     - ``cbf.function_modes``
     - Renamed
   * - ``max_baseline_km``
     - Both
     - ``receptors.max_baseline_km``
     - Renamed
   * - ``number_dish_ids`` (Mid), ``number_station_ids`` (Low)
     - Both
     - ``receptors.receptor_ids``
     - Renamed. The ODT view calls it ``receptors``
   * - ``number_zoom_windows``
     - Both
     - ``observing_modes.spectral.max_zoom_windows``
     - Renamed
   * - ``number_zoom_channels``
     - Both
     - ``observing_modes.spectral.max_zoom_channels``
     - Renamed
   * - ``number_pss_beams``
     - Both
     - ``observing_modes.pss.max_beams``
     - Renamed
   * - ``ps_beam_bandwidth_hz``
     - Both
     - ``observing_modes.pss.beam_bandwidth_hz``
     - Renamed
   * - ``number_pst_beams``
     - Both
     - ``observing_modes.pst.max_beams``
     - Renamed
   * - ``subarray_templates``
     - Both
     - ``repository.get_subarray_templates(telescope, array_assembly)``
     - Moved out of the capabilities: a list of ``SubarrayTemplate``, each
       with its ``name``, ``subarray_type``, ``description`` and
       ``receptor_ids``, a list where the legacy response served
       ``custom_stations``, one comma-separated string
   * - ``allowed_zoom_factors``
     - Low
     - ``observing_modes.spectral.zoom_factors``
     - Renamed and changed: the PDM's zoom factors, so ``[1, 2, 3]`` where the
       legacy field held the multipliers 2**z with 1 for no zoom,
       ``[1, 2, 4, 8]``, and ``[]`` (no zoom) where it held ``[0]``
   * - ``number_stations``
     - Low
     - ``receptors.number_stations``
     - Renamed
   * - ``number_vlbi_beams``
     - Low
     - ``observing_modes.vlbi.max_beams``
     - Renamed
   * - ``number_subarray_beams``
     - Low
     - ``sps.subarray_beams.max_subarray_beams``
     - Renamed
   * - ``number_substations``
     - Low
     - ``sps.subarray_beams.max_substations_per_subarray_beam``
     - Renamed
   * - ``number_beams``
     - Low
     - none
     - Removed: a backwards compatible alias of ``number_subarray_beams`` that
       is no longer supported. The PHT view still serves it, as
       ska-oso-services' PHT response requires it
   * - ``allowed_channel_count_range_min``
     - Mid
     - none
     - Removed: always ``[1]``, as every spectral window has at least one
       channel
   * - ``allowed_channel_count_range_max``
     - Mid
     - ``cbf.max_channels``
     - Renamed and changed: a number, not a list; the most correlated channels
       over all spectral windows, or ``None`` if the OSD sets no limit, where
       the legacy field held 2147483647
   * - ``allowed_channel_width_values_hz``, ``allowed_channel_width_values``
     - Mid
     - ``allowed_channel_width_values_hz``
     - Changed: worked out from ``observing_modes.spectral.zoom_factors``,
       ``observing_modes.continuum.channel_averaging_factors`` and
       ``cbf.fine_channel_width_hz``, which the tmdata stores instead
   * - ``available_receivers``
     - Mid
     - ``receivers``
     - Renamed
   * - ``number_ska_dishes``, ``number_meerkat_dishes``,
       ``number_meerkatplus_dishes``
     - Mid
     - ``receptors.number_ska_dishes``, ``receptors.number_meerkat_dishes``,
       ``receptors.number_meerkatplus_dishes``
     - Renamed
   * - none
     - Mid
     - ``observing_modes.continuum.channel_averaging_factors``,
       ``observing_modes.spectral.zoom_factors``
     - Added: what the channel widths are worked out from


Other fields
~~~~~~~~~~~~~

Fields the legacy capabilities files held beside the capabilities:

* ``constraints``: the elevation limits are in the capabilities'
  ``elevation_limits``, and ``repository.get_constraints(telescope)`` returns
  them with the sun, moon and Jupiter avoidance angles.
* ``quality_attribute_metrics`` (Low):
  ``repository.get_defaults(Telescope.SKA_LOW).quality_attribute_metrics``.
* The SPFRx defaults, which the ODT view serves as Mid's ``spfrx_defaults``:
  ``repository.get_defaults(Telescope.SKA_MID).spfrx_defaults``.


Cycles
~~~~~~~

``get_osd_using_tmdata`` serves a cycle as ``observatory_policy``;
``repository.get_cycle(cycle_id)`` returns it as a ``Cycle``:

.. list-table::
   :header-rows: 1
   :widths: 35 35 30

   * - Legacy field
     - Python API
     - Change
   * - ``cycle_id``, ``cycle_number``
     - ``cycle_id``, ``cycle_number``
     - Unchanged. Cycles are looked up by ``cycle_id``; ``cycle_number`` is
       optional
   * - ``cycle_description``
     - ``description``
     - Renamed
   * - none
     - ``name``
     - Added
   * - ``cycle_information.proposal_open``,
       ``cycle_information.proposal_close``
     - ``proposal_window.opens``, ``proposal_window.closes``
     - Renamed
   * - ``cycle_policies.normal_max_hours``
     - ``proposal_policy.max_observing_hours``
     - Renamed
   * - ``cycle_policies.max_targets``,
       ``cycle_policies.max_observation_setups``,
       ``cycle_policies.max_data_products``
     - ``proposal_policy.max_targets``,
       ``proposal_policy.max_observation_setups``,
       ``proposal_policy.max_data_products``
     - Renamed
   * - ``type``, ``telescope_capabilities``
     - ``telescopes``
     - Changed: for each telescope, a ``CycleTelescope`` with its
       ``array_assembly`` and the policy offered for each ``PolicyType``.
       ``repository.get_cycle_capabilities(cycle_id)`` returns the merged
       capabilities for each telescope and policy type

For how cycles, policy types and policies fit together, see
:ref:`how capabilities are built <how-capabilities-are-built>` in the guide.
