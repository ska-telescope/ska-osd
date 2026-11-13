############
Change Log
############

All notable changes to this project will be documented in this file.
This project adheres to `Semantic Versioning <http://semver.org/>`_.

Unreleased
**********
* [BREAKING] Removed the REST API: the FastAPI app, its Helm charts and OCI image, and
  the ``/osd``, ``/cycle``, ``/osd_release`` and ``/semantic_validation`` endpoints.
  The OSD is now a Python library only
* [BREAKING] Removed semantic validation, ``ska_ost_osd.telvalidation``
* [BREAKING] Removed the code behind the ``PUT /osd`` and ``/osd_release`` endpoints:
  ``update_osd_file`` and ``add_new_data_storage`` in ``ska_ost_osd.osd.osd``,
  ``ska_ost_osd.osd.version_mapping``, ``ska_ost_osd.osd.common.gitlab_helper``,
  ``ska_ost_osd.osd.common.utils``, ``ska_ost_osd.osd.models.models`` and
  ``CapabilityError``
* [BREAKING] Removed ``ska_ost_osd.common``, including the FastAPI
  ``generic_exception_handler``
* Removed the ``fastapi``, ``astropy`` and ``simpleeval`` dependencies
* [BREAKING] Renamed the ``Telescope`` members to ``SKA_MID`` and ``SKA_LOW``, with
  the values ``ska_mid`` and ``ska_low`` of the PDM's ``TelescopeType``. The
  ``telescope`` of a capability set in the PHT view changes to match.
  ``get_osd_using_tmdata`` still accepts ``"mid"`` and ``"low"``
* [BREAKING] Renamed the subarray templates in ``subarray_template_library.json``
  to start with ``SKA_MID_`` and ``SKA_LOW_``
* [BREAKING] Define multiple cycles through a single TelModel backend in ``tmdata/cycles``
* Each cycle file in ``tmdata/cycles`` may have any name. A cycle has a unique ``id``,
  a ``name``, a ``description``, an optional unique ``number``, a ``proposal_window``,
  a ``proposal_policy`` and ``capabilities``: for each telescope, keyed ``ska_low`` or
  ``ska_mid``, its ``array_assembly`` and the policy offered for each policy type
  (``science_verification``, ``shared_risk`` or ``standard_operations``). A policy,
  in ``telescopes/<telescope>/policies``, has an ``id`` and sets only what it changes
  of the array assembly a cycle pairs it with; the repository returns the two
  merged. Low's ``AA2_SV`` is now the ``AA2_SV`` policy applied to ``AA2``, which the
  legacy response still serves as ``AA2_SV``.
  [BREAKING] The ODT view serves only array assemblies, so it no longer lists Low's
  ``AA2_SV``. The
  legacy response and the PHT view serve a cycle offering one policy type, under the
  old field names: ``cycle_id``, ``cycle_description``, ``cycle_number``, ``type``
  (``Science Verification``, ``Shared Risk`` or ``Proposal``), ``cycle_information``
  (the ``cycle_id`` and the proposal dates), ``cycle_policies`` (with
  ``max_observing_hours`` as ``normal_max_hours``) and ``telescope_capabilities``
  (keyed ``Mid`` and ``Low``).
  ``get_osd_using_tmdata`` selects a cycle by its ``number``, so can't select one without
* A cycle's ``cycle_number`` may be 0, for Cycle 0
* [BREAKING] Users pass a TMData client to public API functions instead of OSD creating one from ``tmdata/version_mapping``
* [BREAKING] Removed ``number_beams``, a duplicate of ``number_subarray_beams``, from
  SKA-Low's capability sets, including in the legacy response and the PHT view
* [BREAKING] Removed the duplicate ``coarse_channel_width`` from
  ``low_capabilities.json``; use ``coarse_channel_width_hz``
* [BREAKING] Removed the sun, moon and Jupiter avoidance angles from the capabilities
  files; they are defined in ``mid_defaults.json`` and ``low_defaults.json``
* Added a ``basic_capabilities.json`` for each telescope, holding its
  receiver bands as ``frequency_bands`` (Mid) or its one ``frequency_band`` (Low), its
  ``elevation_limits`` and, for Low, its ``coarse_channels`` and the channels each of
  its ``modes`` divides them into. The legacy response and the views still serve Low's
  coarse channels and channels per mode as fields of its band.
  ``mid_capabilities.json`` and ``low_capabilities.json`` are kept for older releases
  but are no longer read
* Moved telescope capability sets to standalone tmdata files, one per array assembly,
  in ``telescopes/<telescope>/array_assemblies``. Low's stations are in
  ``stations``, as ``number_stations``, ``max_baseline_km`` and ``ids``, and Mid's
  dishes in ``dishes``, as ``number_ska_dishes``, ``number_meerkat_dishes``,
  ``number_meerkatplus_dishes``, ``max_baseline_km`` and ``ids``. The legacy response
  serves these fields flat, with the IDs as ``number_station_ids`` or
  ``number_dish_ids``; the views serve the IDs as ``receptors``. Mid's receivers are
  listed as ``receivers``, served as ``available_receivers``.
  Mid's channel widths are only stored as ``allowed_channel_width_values_hz``; the
  legacy response and the PHT view also serve them as ``allowed_channel_width_values``.
  Low's zoom windows are in ``modes.spectral``, as ``max_zoom_windows``,
  ``max_zoom_channels`` (per window) and ``zoom_factors``, and its beams in
  ``modes.pss``, ``modes.pst`` and ``modes.vlbi`` as ``max_beams``, with the pulsar
  search beam bandwidth as ``modes.pss.beam_bandwidth_hz``; Mid's zoom windows and
  beams are in its ``modes`` in the same way, without zoom factors. The legacy
  response and the PHT view serve them as ``number_zoom_windows``,
  ``number_zoom_channels``,
  ``allowed_zoom_factors``, ``number_<mode>_beams`` and ``ps_beam_bandwidth_hz``;
  the ODT view serves ``number_pst_beams``. Low's subarray beams are in
  ``subarray_beams``, as ``max_subarray_beams`` and
  ``max_substations_per_subarray_beam``, which the legacy response and the views
  serve as ``number_subarray_beams`` and ``number_substations``
* Moved each telescope's current tmdata files under ``telescopes/ska_low`` and
  ``telescopes/ska_mid``, named by the ``Telescope`` values, with its defaults in
  ``defaults.json``. The legacy files stay at their old paths for older releases and
  for consumers that read them directly, including copies of ``mid_defaults.json``
  and ``low_defaults.json``
* Moved subarray templates to a tmdata file per telescope and array assembly; each
  capability set names its ``array_assembly`` instead of template wildcard patterns
* [BREAKING] Removed ``ska_ost_osd.osd.template_mapping``; ``get_osd_using_tmdata``
  reads each capability set's templates from its array assembly's file
* The PHT views take ``include_subarray_templates`` to serve each capability set's
  subarray templates, as ``get_osd_using_tmdata`` does with ``process_templates``
* Removed the unused semantic validation constants from ``tmdata/instrument``
* ``get_osd_using_tmdata`` queries without a cycle now return the complete capability
  catalogue
* Removed ``osd-pre-release``, ``osd-tmdata-publish`` and ``release.sh``
* Added proposal cycle data to the release-cycle version mapping.
* Added Pydantic storage models for the tmdata files: ``MidDefaultsFile`` and
  ``LowDefaultsFile``, ``CycleFile``
  (``cycles/*.json``) and ``SubarrayTemplateLibraryFile``, in
  ``ska_ost_osd.osd.adapters.tmdata.models``
* ``Cycle`` reads when its proposal window ``opens`` and ``closes`` as timezone-aware
  datetimes, a date without a timezone is rejected.
* Added a test that validates the real tmdata files against these models
* Added ``OSDRepository`` (``ska_ost_osd.osd.repository``), the interface for
  reading cycles, capability sets, basic capabilities, constraints, defaults and
  subarray templates as Pydantic models, and ``TMDataRepository``
  (``ska_ost_osd.osd.adapters.tmdata``), which implements it over a TMData client
* Added ``ska_ost_osd.osd.views``: the configuration ska-oso-services serves to the
  ODT (``views.odt``) and the cycle data it serves to the PHT (``views.pht``), built
  from an ``OSDRepository``. The views serialise with the names their consumers
  read by default, without ``by_alias=True``
* Raised the minimum pydantic version to 2.11, for ``serialize_by_alias``
* Bump the build and runtime base images to ``ska-build-python-ubuntu26:1.1.2`` and
  ``ska-python-ubuntu26:1.1.2`` to pick up the OpenSSL DTLS retransmission fix

7.0.0
**********
* [BREAKING] Change Mid's SPFRx sync_pps default from false to unset
* Migrated build and developer tooling from Poetry to uv, and from
  black/isort/flake8/pylint to ruff.
* Minimum supported Python version is now 3.11, testing on Python 3.14.
* Upgraded astropy to 8.x, which ships stable-ABI wheels for Python 3.11 to 3.14.
* Use FastAPI dependency injection to handle TMData clients
* [BUGFIX] Fix number_zoom_windows for AA2_SV to be 1 instead of 16

6.0.9
**********
* Update version_mapping (missing from 6.0.8)

6.0.8
**********
* Updated OSDModel validator for case where cycle_id=0 and array_assembly
* Removed upper bound version constraint on FastAPI and ska-ser-logging to unblock upgrades for downstream projects.

6.0.7
**********
* Fix client to accept 0 as a valid cycle number/ID
* Change LOW SV cycle number to 1 to be forwards compatible

6.0.6
**********
* Use ISO 8601 format for cycle proposal_open and proposal_close timestamps
* Update LOW SV cycle 0 policy data for PHT testing; drop unused cycle 1

6.0.5
**********
* Updated MID and LOW capabilities TMData for better integration with other OSO applications
* Migrated secret management from Secrets Store CSI Driver to Vault Secrets Operator (VaultStaticSecret) for improved reliability and consistency with other OSO services.

6.0.4
**********
* Fixed RTD Docs issue.

6.0.3
**********
* Made `tmdata-publish` and `osd-tmdata-publish` jobs manual for now.

6.0.2
**********
* Mock autodoc import for ska-telmodel-client

6.0.1
**********
* Fixed release

6.0.0
**********
* Added constraints to both MID and LOW capabilities
* Updated the available dishes for MID AA0.5 and AA1
* Updated dependencies to use ska-telmodel-client
* Removed redundant semantic validation test
* Added SonarQube for static analysis of code quality

5.2.1
**********
* Fixed Get cycle list API.
* Fixed get_cycle_list() method to use it from when we installed OSD as library.

5.2.0
**********
* Added capabilities for LOW Science Verification AA2_SV
* Updated basic capabilities for LOW telescope

5.1.0
***********
* Created a new cycle policy for Low telescope for science verification.

5.0.0
***********
* Added AA1 and AA2 rule support.
* Created new Mid_ITF and Low_ITF from MID AA0.5 and LOW AA1.
* Modified GET PUT /OSD API to fetch and modify the newly added Mid_ITF and Low_ITF values.
* Fixed sideband for 5b subband 3 from 'high' to 'low'
* Removed unused SKUID python dependency
* [BREAKING] Added subarray template support for MID / LOW capabilities.

4.2.2
***********
* NAK-1352 Refactor handling of TelModel data sources including default
* Added band 5b to the available receivers for Mid AA0.5

4.2.1
***********
* Fix issue due to now running `make osd-pre-release`

4.2.0
***********
* Added support for `array_assembly` in `semantic_validation` API
* Updated doc strings to sphinx style format
* Refactoring of test cases
* Added support to update `openapi.json` file using make
* Add support for sub_bands in band 5b and adjusted 5b frequency range.
* Modified rules to ensure band 5b setups are specified in the B1 frequency range.

4.1.0
*****
* NAK-1300 Migrate tmdata files to schmea-mapped directories
* NAK-1300 Update to ska-telmodel 1.23.2 for key aliasing

4.0.0
**********
* Migrated APIs from Flask to FastAPI
* [BREAKING] Refactored folder structure
* [BREAKING] Separated OSD and TelValidation modules
* [BREAKING] Introduced a generalized response format

3.1.1
**********
* Fixed version mapping file path issue while checking cycle_id present or not.

3.1.0
**********
* Decoupled Release process of TMData from `ska-ost-osd` source code.
* Now OSD User can publish TMData automatically from OSD UI Editor.
* Introduced new APIs to automate TMData release process.
* Updated OSD User guide.

3.0.0
**********
* [BREAKING] Added `number_dish_ids` in Mid Capabilities.
* [BREAKING] Removed `number_channel` key.
* [BREAKING] Converted `allowed_channel_count_range_min` and `allowed_channel_count_range_max` string type to list.
* [BREAKING] Added `allowed_channel_width_values` key.
* Updated Docs for Mid and Low Capabilities.
* Refactored Test cases and restructured Test folder.

2.3.1
**********
* Updated to deepdiff version 7.0.0.
* Updated to pydantic version 2.10.3

2.3.0
********
* Upgraded astropy version to 6.1 from 5.1.

2.2.1
********
* Fixed Semantic Validation error message bug.
* Fixed OSD document issue.
  - Changelog was not reflecting earlier so fixed that.
  - RTD build was failing on pipeline.

2.2.0
*******
* Added VALIDATION_STRICTNESS environment variable to enable the functionality of semantic validation to turn on/off.

2.1.0
**************
* Verify OSD version mapping behaviour along with remove hard coded error messages checks from OSD code.
* Combined osd and semantic API input validations.
* Updated the telmodel tag to 0.19.4
  - TMC-Mid Configure v4.1: Added pointing.groups to bring OSO/TMC-Mid pointing interface up to date with ADR-63 (sky coordinates), ADR-106 (tracking and mapping), and ADR-94 (holography).
  - TMC-Mid Configure v4.1: Deprecated pointing.target
  - SKB-462 resolved

2.0.1
*****
* Added CHANGELOG.rst into doc folder.
* Reverted ArgumentType of "TMData" in function "semantic_validate" and ReturnType of semantic_validate function
  which had been changed during refactoring and causing linting issue in CDM.

2.0.0
*****
* Removed complex code and increase readability
* Fixed independance semantic validation call issue.
* Modified test cases added parameterized test cases.
* Added semantic validation for LOW SB.
* MID and Low capabilities enhancement to support validation.

1.0.3
******
* Improve API level validation for OSD API's

1.0.2
******
* Removed requirement.txt file from docs folder.

1.0.1
******
* Fixed pipeline issue after release tag for 1.0.0 version.
* Fixed RTD documentation issue.
* Fixed minor variable names.


1.0.0
******

* Decoupled and added of Semantic Validation and OSD functionalities from ska-telmodel
* The functionalities have been exposed as a service
