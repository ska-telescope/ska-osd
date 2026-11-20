OSD Model
---------

.. contents::


Folder Structure
~~~~~~~~~~~~~~~~

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
    └── version_mapping                      (legacy)
        ├── cycle_gitlab_release_version_mapping.json
        └── latest_release.txt

The current files are in ``cycles`` and ``telescopes``. The files in
``version_mapping`` are kept for releases of the OSD before 8.0.0, which read
them to find the release whose tmdata to read, as described in
:ref:`legacy-publishing`. Only the deprecated ``get_osd_latest_version`` reads
them in the current code.

Each of these files names what it describes in a field, so their file names
don't matter:

.. list-table::
   :header-rows: 1

   * - File
     - Identified by
     - Holds
   * - ``basic_capabilities.json``
     - ``telescope``
     - what is fixed for the telescope: Mid's receiver bands
       (``frequency_bands``) or Low's one ``frequency_band``, the
       ``elevation_limits``, for Mid, in ``cbf``, the
       ``frequency_slice_bandwidth_hz`` each FSP processes and the
       ``fine_channel_width_hz`` it divides a slice into, and for Low, in
       ``sps``, its ``coarse_channels`` and, in ``observing_modes``, how each
       observing mode divides them
   * - ``array_assemblies/*.json``
     - ``array_assembly``
     - what one array assembly offers, such as ``AA2``: its receptors,
       bandwidth, its FSPs, CBF function modes and (Mid) channel limit in
       ``cbf``, for Low its
       subarray beams in ``sps``, and, in
       ``observing_modes``, each observing mode's beams, zoom windows and
       zoom factors and, for Mid, its channel averaging factors
   * - ``policies/*.json``
     - ``policy``
     - the rules a cycle applies to an array assembly, such as ``AA2_SV``:
       only the fields it changes
   * - ``subarray_templates/*.json``
     - ``array_assembly``
     - the subarray templates an array assembly offers, such as ``AA*``,
       whose file is ``AASTAR.json``
   * - ``cycles/*.json``
     - ``cycle_id``
     - a cycle: its proposal window and policy, and in ``telescopes``, for
       each telescope, its array assembly and the policy offered for each
       policy type

.. _how-capabilities-are-built:

How capabilities are built
~~~~~~~~~~~~~~~~~~~~~~~~~~

What a telescope offers, its *capabilities*, is built from three layers, each
changed for its own reason:

.. code-block:: text

    capabilities = basic capabilities           fixed for the telescope
                 + array assembly               a construction milestone
                 with a policy's changes        SciOps' access rules, if a policy applies

Basic capabilities
    What the telescope's design fixes, however much of it is built: Mid's
    receiver bands, frequency slice bandwidth and fine channel width, Low's
    frequency band and coarse channels, and the elevation limits. They change
    only if the design does.

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
  a group: ``observing_modes.spectral`` takes its channels per coarse channel from Low's
  basic capabilities and its zoom windows from the array assembly.
* The result names its ``telescope``, ``array_assembly`` and ``policy``.

Within the files, fields are grouped by the part of the telescope that
provides them, or by observing mode:

``cbf``
    The correlator-beamformer (CBF): Mid's frequency slice bandwidth and fine
    channel width, and for each array assembly its frequency slice processors
    (FSPs), the function modes it runs and, for Mid, ``max_channels``: the most
    correlated channels over all spectral windows, or ``null`` if the OSD sets
    no limit (each spectral window has at least one channel, so there is no
    minimum). In a scheduling block, it limits the ``csp_configuration``'s
    ``midcbf`` or ``lowcbf``.

``sps`` (Low only)
    The stations' signal processing (SPS): the coarse channels the stations
    divide the band into, and the subarray beams they form. MCCS configures
    it: in a scheduling block, the subarray beams are in the
    ``mccs_allocation``, and the spectral windows the coarse channels carry
    are in the ``csp_configuration``.

``observing_modes``
    What each observing mode offers, whichever part of the telescope provides
    it: channels, zoom windows, zoom factors, Mid's channel averaging factors,
    and beams. Zoom factors are the PDM's: zoom factor *z* narrows a spectral
    window's channels by 2**z, and 0, which means no zoom (continuum), is never
    listed, so ``[]`` means no zoom is offered.

A cycle pairs each telescope's array assembly with the policy offered for each
policy type. Low AA2 Science Verification, for example, is the ``AA2`` array
assembly with the ``AA2_SV`` policy, which offers one zoom window, one PST beam
and no PSS beams. The cycles, the three policy types (science verification,
shared risk and standard operations) and what each offers as the telescopes are
built follow SKAO's `Timeline to Science
<https://www.skao.int/en/science-users/647/timeline-science>`_.

Subarray Template Support
~~~~~~~~~~~~~~~~~~~~~~~~~

A subarray template is a named set of receptors from an array assembly. Each
telescope's templates are stored by array assembly, one file in
``telescopes/<telescope>/subarray_templates`` for each, naming its
``array_assembly`` and listing its templates:

.. code-block:: json

    {
        "array_assembly": "AA2",
        "templates": [
            {
                "name": "SKA_LOW_FULL_AA2",
                "subarray_type": "AA2",
                "receptor_ids": [],
                "description": "Full SKA-Low array, AA2 release."
            }
        ]
    }

An array assembly offers the templates in the file that names it; one with no
template file, such as the ITFs, offers none.

Reading the templates
`````````````````````

* The repository's ``get_subarray_templates(telescope, array_assembly)`` returns
  an array assembly's templates as a list of ``SubarrayTemplate`` models.
