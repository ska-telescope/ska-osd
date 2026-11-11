"""The models expected from the test copy of the tmdata in tests/tmdata,
written out field by field so the repository is checked against the files
rather than against each other."""

from datetime import datetime, timezone

from ska_ost_osd.osd.adapters.tmdata.models import (
    AvoidanceConstraints,
    CycleFile,
    LowCapabilitySetFile,
    LowDefaultsFile,
    MidCapabilitySetFile,
    MidCSPConfigurationDefaults,
    MidDefaultsFile,
    MidTargetDefaults,
    SubarrayTemplateLibraryFile,
)
from ska_ost_osd.osd.models.capabilities import (
    Band5bSubband,
    LowBasicCapabilities,
    LowCapabilitySet,
    LowCBFMode,
    LowFrequencyBand,
    MidBasicCapabilities,
    MidCapabilitySet,
    MidCBFMode,
    MidFrequencyBand,
)
from ska_ost_osd.osd.models.constraints import Constraints, ElevationLimits
from ska_ost_osd.osd.models.cycles import (
    Cycle,
    CycleInformation,
    CyclePolicies,
    TelescopeCapabilities,
)
from ska_ost_osd.osd.models.defaults import (
    CSPSPFRx,
    DefaultNoiseDiodeMode,
    LowCBFMetrics,
    LowDefaults,
    LowQualityAttributeMetrics,
    MidDefaults,
    PeriodicNoiseDiode,
    PseudoRandomNoiseDiode,
    SPFRxParameters,
    SyncPPS,
    TargetSPFRx,
)
from ska_ost_osd.osd.models.subarray_templates import SubarrayTemplate, SubarrayType
from ska_ost_osd.osd.views.odt import (
    Configuration,
    ConfigurationLowCBFMetrics,
    ConfigurationLowQualityAttributeMetrics,
    LowConfiguration,
    LowConfigurationCapabilitySet,
    MidConfiguration,
    MidConfigurationCapabilitySet,
)
from ska_ost_osd.osd.views.pht import (
    CycleCapabilities,
    CycleConfiguration,
    CycleTelescopeCapabilities,
    LowCycleCapabilities,
    MidCycleBasicCapabilities,
    MidCycleCapabilities,
    ObservatoryPolicy,
)

# tests/tmdata/cycles/TEST_SKAO_2027_Low_AA1_SV.json
CYCLE_1 = Cycle(
    cycle_number=1,
    cycle_id="TEST_SKAO_2027_Low_AA1_SV",
    type="Science Verification",
    cycle_description="TEST Low AA1 Science Verification",
    cycle_information=CycleInformation(
        cycle_id="TEST_SKAO_2027_1",
        proposal_open=datetime(2026, 3, 27, 12, 0, tzinfo=timezone.utc),
        proposal_close=datetime(2027, 4, 1, 15, 0, tzinfo=timezone.utc),
    ),
    cycle_policies=CyclePolicies(
        normal_max_hours=100.0,
        max_targets=1,
        max_observation_setups=1,
        max_data_products=1,
    ),
    telescope_capabilities=TelescopeCapabilities(ska_mid=None, ska_low="AA1"),
)

# tests/tmdata/cycles/TEST_SKAO_2027_AA2_Proposal.json
CYCLE_2 = Cycle(
    cycle_number=2,
    cycle_id="TEST_SKAO_2027_AA2_Proposal",
    type="Proposal",
    cycle_description="TEST AA2 Proposal",
    cycle_information=CycleInformation(
        cycle_id="TEST_SKAO_2027_2",
        proposal_open=datetime(2026, 3, 27, 12, 0, tzinfo=timezone.utc),
        proposal_close=datetime(2027, 4, 1, 15, 0, tzinfo=timezone.utc),
    ),
    cycle_policies=CyclePolicies(
        normal_max_hours=100.0,
        max_targets=3,
        max_observation_setups=2,
        max_data_products=2,
    ),
    telescope_capabilities=TelescopeCapabilities(ska_mid="AA2", ska_low="AA2"),
)

# tests/tmdata/cycles/TEST_SKAO_2027_Low_AA1_SV.json, as stored
CYCLE_1_FILE = CycleFile(
    cycle_number=1,
    cycle_id="TEST_SKAO_2027_Low_AA1_SV",
    type="Science Verification",
    cycle_description="TEST Low AA1 Science Verification",
    cycle_information=CycleInformation(
        cycle_id="TEST_SKAO_2027_1",
        proposal_open=datetime(2026, 3, 27, 12, 0, tzinfo=timezone.utc),
        proposal_close=datetime(2027, 4, 1, 15, 0, tzinfo=timezone.utc),
    ),
    cycle_policies=CyclePolicies(
        normal_max_hours=100.0,
        max_targets=1,
        max_observation_setups=1,
        max_data_products=1,
    ),
    telescope_capabilities=TelescopeCapabilities(ska_mid=None, ska_low="AA1"),
)

# tests/tmdata/cycles/TEST_SKAO_2027_AA2_Proposal.json, as stored
CYCLE_2_FILE = CycleFile(
    cycle_number=2,
    cycle_id="TEST_SKAO_2027_AA2_Proposal",
    type="Proposal",
    cycle_description="TEST AA2 Proposal",
    cycle_information=CycleInformation(
        cycle_id="TEST_SKAO_2027_2",
        proposal_open=datetime(2026, 3, 27, 12, 0, tzinfo=timezone.utc),
        proposal_close=datetime(2027, 4, 1, 15, 0, tzinfo=timezone.utc),
    ),
    cycle_policies=CyclePolicies(
        normal_max_hours=100.0,
        max_targets=3,
        max_observation_setups=2,
        max_data_products=2,
    ),
    telescope_capabilities=TelescopeCapabilities(ska_mid="AA2", ska_low="AA2"),
)

# The policy in the legacy response for cycle 1: tests/tmdata/cycles/TEST_SKAO_2027_Low_AA1_SV.json
# as stored, with the telescopes keyed Mid and Low
CYCLE_1_LEGACY_OBSERVATORY_POLICY = {
    "cycle_number": 1,
    "cycle_id": "TEST_SKAO_2027_Low_AA1_SV",
    "type": "Science Verification",
    "cycle_description": "TEST Low AA1 Science Verification",
    "cycle_information": {
        "cycle_id": "TEST_SKAO_2027_1",
        "proposal_open": "2026-03-27T12:00:00.000Z",
        "proposal_close": "2027-04-01T15:00:00.000Z",
    },
    "cycle_policies": {
        "normal_max_hours": 100.0,
        "max_targets": 1,
        "max_observation_setups": 1,
        "max_data_products": 1,
    },
    "telescope_capabilities": {"Low": "AA1"},
}

# tests/tmdata/telescopes/ska_mid/capabilities/AA1.json and AA2.json
MID_AA1 = MidCapabilitySet(
    name="AA1",
    receptors=["SKA001", "SKA002", "SKA003", "SKA004"],
    available_bandwidth_hz=800_000_000,
    number_pst_beams=1,
    number_fsps=4,
    max_baseline_km=1.5,
    number_zoom_windows=0,
    number_zoom_channels=0,
    number_pss_beams=0,
    ps_beam_bandwidth_hz=400_000_000,
    allowed_channel_width_values_hz=[13440],
    allowed_channel_count_range_min=[1],
    allowed_channel_count_range_max=[58982],
    available_receivers=["Band_1", "Band_2", "Band_5b"],
    cbf_modes=[MidCBFMode.CORRELATION, MidCBFMode.PST],
    number_ska_dishes=4,
    number_meerkat_dishes=0,
    number_meerkatplus_dishes=0,
)

MID_AA2 = MidCapabilitySet(
    name="AA2",
    receptors=[
        "SKA001",
        "SKA002",
        "SKA003",
        "SKA004",
        "SKA005",
        "SKA006",
        "SKA007",
        "SKA008",
    ],  # fmt: skip
    available_bandwidth_hz=800_000_000,
    number_pst_beams=1,
    number_fsps=8,
    max_baseline_km=1.5,
    number_zoom_windows=0,
    number_zoom_channels=0,
    number_pss_beams=0,
    ps_beam_bandwidth_hz=400_000_000,
    allowed_channel_width_values_hz=[13440],
    allowed_channel_count_range_min=[1],
    allowed_channel_count_range_max=[58982],
    available_receivers=["Band_1", "Band_2", "Band_5a", "Band_5b"],
    cbf_modes=[MidCBFMode.CORRELATION, MidCBFMode.PST],
    number_ska_dishes=8,
    number_meerkat_dishes=0,
    number_meerkatplus_dishes=0,
)

# tests/tmdata/telescopes/ska_mid/basic_capabilities.json
MID_BASIC_CAPABILITIES = MidBasicCapabilities(
    frequency_bands=[
        MidFrequencyBand(
            rx_id="Band_1", min_frequency_hz=350_000_000, max_frequency_hz=1_050_000_000
        ),
        MidFrequencyBand(
            rx_id="Band_2", min_frequency_hz=950_000_000, max_frequency_hz=1_760_000_000
        ),
        MidFrequencyBand(
            rx_id="Band_3",
            min_frequency_hz=1_650_000_000,
            max_frequency_hz=3_050_000_000,
        ),
        MidFrequencyBand(
            rx_id="Band_4",
            min_frequency_hz=2_800_000_000,
            max_frequency_hz=5_180_000_000,
        ),
        MidFrequencyBand(
            rx_id="Band_5a",
            min_frequency_hz=4_600_000_000,
            max_frequency_hz=8_500_000_000,
        ),
        MidFrequencyBand(
            rx_id="Band_5b",
            min_frequency_hz=11_450_000_000,
            max_frequency_hz=13_510_000_000,
            band5b_subbands=[
                Band5bSubband(
                    sub_band=1,
                    min_frequency_hz=11_450_000_000,
                    max_frequency_hz=12_150_000_000,
                    lo_frequency_hz=11_100_000_000,
                    sideband="high",
                ),
                Band5bSubband(
                    sub_band=2,
                    min_frequency_hz=12_810_000_000,
                    max_frequency_hz=13_510_000_000,
                    lo_frequency_hz=13_860_000_000,
                    sideband="low",
                ),
                Band5bSubband(
                    sub_band=3,
                    min_frequency_hz=12_150_000_000,
                    max_frequency_hz=12_850_000_000,
                    lo_frequency_hz=11_100_000_000,
                    sideband="low",
                ),
            ],
        ),
    ],
    elevation_limits=ElevationLimits(min_elevation_deg=15.0, max_elevation_deg=90.0),
)

# The capability sets as stored: keyed by name, with the receptors under the
# file's own key, no telescope, and the array assembly that keys their
# subarray templates (in the test tmdata, the same as the name)
MID_CAPABILITY_SET_FILES = {
    capability_set.name: MidCapabilitySetFile(
        number_dish_ids=capability_set.receptors,
        array_assembly=capability_set.name,
        **capability_set.model_dump(exclude={"name", "telescope", "receptors"}),
    )
    for capability_set in (MID_AA1, MID_AA2)
}

# tests/tmdata/telescopes/ska_low/capabilities/AA1.json and AA2.json
LOW_AA1 = LowCapabilitySet(
    name="AA1",
    receptors=[345, 346, 347, 348],
    number_stations=4,
    number_substations=0,
    number_subarray_beams=1,
    max_baseline_km=3.0,
    available_bandwidth_hz=75_000_000.0,
    cbf_modes=[LowCBFMode.VIS, LowCBFMode.PST],
    number_zoom_windows=0,
    number_zoom_channels=0,
    number_pss_beams=0,
    number_pst_beams=1,
    number_vlbi_beams=0,
    ps_beam_bandwidth_hz=75_000_000.0,
    number_fsps=6,
    allowed_zoom_factors=[0],
)

LOW_AA2 = LowCapabilitySet(
    name="AA2",
    receptors=[345, 346, 347, 348, 349, 350, 351, 352],
    number_stations=8,
    number_substations=512,
    number_subarray_beams=8,
    max_baseline_km=6.0,
    available_bandwidth_hz=75_000_000.0,
    cbf_modes=[LowCBFMode.VIS, LowCBFMode.PST],
    number_zoom_windows=0,
    number_zoom_channels=0,
    number_pss_beams=0,
    number_pst_beams=1,
    number_vlbi_beams=0,
    ps_beam_bandwidth_hz=75_000_000.0,
    number_fsps=6,
    allowed_zoom_factors=[1, 2, 4, 8],
)

# The band in tests/tmdata/telescopes/ska_low/basic_capabilities.json
LOW_FREQUENCY_BAND = LowFrequencyBand(
    min_frequency_hz=50_000_000.0,
    max_frequency_hz=350_000_000.0,
    min_coarse_channel=64,
    max_coarse_channel=447,
    coarse_channel_width_hz=781_250.0,
    number_continuum_channels_per_coarse_channel=144,
    number_zoom_channels_per_coarse_channel=432,
    number_pst_channels_per_coarse_channel=216,
    number_pss_channels_per_coarse_channel=54,
)

# tests/tmdata/telescopes/ska_low/basic_capabilities.json
LOW_BASIC_CAPABILITIES = LowBasicCapabilities(
    frequency_bands=[LOW_FREQUENCY_BAND],
    elevation_limits=ElevationLimits(min_elevation_deg=45.0, max_elevation_deg=90.0),
)

LOW_CAPABILITY_SET_FILES = {
    capability_set.name: LowCapabilitySetFile(
        number_station_ids=capability_set.receptors,
        array_assembly=capability_set.name,
        **capability_set.model_dump(exclude={"name", "telescope", "receptors"}),
    )
    for capability_set in (LOW_AA1, LOW_AA2)
}

# The defaults in tests/tmdata/telescopes/ska_mid/defaults.json
MID_DEFAULTS = MidDefaults(
    spfrx_defaults=SPFRxParameters(
        target_spfrx=TargetSPFRx(
            attenuation_1_x=10.0,
            attenuation_1_y=10.0,
            attenuation_2_x=10.0,
            attenuation_2_y=10.0,
            noise_diode_options=[
                PeriodicNoiseDiode(
                    period_ms=1000.0, duty_cycle_ms=500.0, phase_shift_ms=0.0
                ),
                PseudoRandomNoiseDiode(binary_polynomial=0, seed=0, dwell_ms=0.0),
            ],
            default_noise_diode_mode=DefaultNoiseDiodeMode.OFF,
        ),
        csp_spfrx=CSPSPFRx(sync_pps=SyncPPS.UNSET, saturation_threshold=0.2),
    ),
)

# The whole of tests/tmdata/telescopes/ska_mid/defaults.json
MID_DEFAULTS_FILE = MidDefaultsFile(
    constraints=AvoidanceConstraints(
        sun_avoidance_angle_deg=30.0,
        moon_avoidance_angle_deg=10.0,
        jupiter_avoidance_angle_deg=10.0,
    ),
    target=MidTargetDefaults(
        dish_spfrx_params=MID_DEFAULTS.spfrx_defaults.target_spfrx
    ),
    csp_configuration=MidCSPConfigurationDefaults(
        spfrx=MID_DEFAULTS.spfrx_defaults.csp_spfrx
    ),
)

# The defaults in tests/tmdata/telescopes/ska_low/defaults.json
LOW_DEFAULTS = LowDefaults(
    quality_attribute_metrics=LowQualityAttributeMetrics(
        cbf=LowCBFMetrics(processors_ready_percent=100, alveo_configured_percent=100)
    ),
)

# The whole of tests/tmdata/telescopes/ska_low/defaults.json
LOW_DEFAULTS_FILE = LowDefaultsFile(
    constraints=AvoidanceConstraints(
        sun_avoidance_angle_deg=30.0,
        moon_avoidance_angle_deg=10.0,
        jupiter_avoidance_angle_deg=10.0,
    ),
    quality_attribute_metrics=LOW_DEFAULTS.quality_attribute_metrics,
)

# Elevation limits from tests/tmdata/telescopes/ska_mid/basic_capabilities.json and
# avoidance angles from defaults.json
MID_CONSTRAINTS = Constraints(
    min_elevation_deg=15.0,
    max_elevation_deg=90.0,
    sun_avoidance_angle_deg=30.0,
    moon_avoidance_angle_deg=10.0,
    jupiter_avoidance_angle_deg=10.0,
)

# Elevation limits from tests/tmdata/telescopes/ska_low/basic_capabilities.json and
# avoidance angles from defaults.json
LOW_CONSTRAINTS = Constraints(
    min_elevation_deg=45.0,
    max_elevation_deg=90.0,
    sun_avoidance_angle_deg=30.0,
    moon_avoidance_angle_deg=10.0,
    jupiter_avoidance_angle_deg=10.0,
)

# tests/tmdata/telescopes/<telescope>/subarray_templates/<array assembly>.json
MID_FULL_AA2_TEMPLATE = SubarrayTemplate(
    name="SKA_MID_FULL_AA2",
    subarray_type=SubarrayType.CUSTOM,
    custom_stations=[
        "SKA001",
        "SKA002",
        "SKA003",
        "SKA004",
        "SKA005",
        "SKA006",
        "SKA007",
        "SKA008",
    ],  # fmt: skip
    description="TEST full Mid AA2 array.",
)
LOW_TEST_AA1_TEMPLATE = SubarrayTemplate(
    name="SKA_LOW_TEST_AA1",
    subarray_type=SubarrayType.CUSTOM,
    custom_stations=["S8-1", "S8-2"],
    description="TEST Low AA1 subset of stations.",
)
LOW_FULL_AA2_TEMPLATE = SubarrayTemplate(
    name="SKA_LOW_FULL_AA2",
    subarray_type=SubarrayType.AA2,
    custom_stations=[],
    description="TEST full Low AA2 array.",
)
LOW_TEST_AA2_TEMPLATE = SubarrayTemplate(
    name="SKA_LOW_TEST_AA2",
    subarray_type=SubarrayType.CUSTOM,
    custom_stations=["S8-1", "S8-2", "S8-3", "S8-4"],
    description="TEST Low AA2 subset of stations.",
)

MID_AA2_SUBARRAY_TEMPLATE_LIBRARY_FILE = SubarrayTemplateLibraryFile(
    templates=[MID_FULL_AA2_TEMPLATE]
)

LOW_AA1_SUBARRAY_TEMPLATE_LIBRARY_FILE = SubarrayTemplateLibraryFile(
    templates=[LOW_TEST_AA1_TEMPLATE]
)

LOW_AA2_SUBARRAY_TEMPLATE_LIBRARY_FILE = SubarrayTemplateLibraryFile(
    templates=[LOW_FULL_AA2_TEMPLATE, LOW_TEST_AA2_TEMPLATE]
)

# The ODT configuration view of tests/tmdata: what ska-oso-services serves
# from GET /configuration
CONFIGURATION = Configuration(
    ska_mid=MidConfiguration(
        frequency_band=MID_BASIC_CAPABILITIES.frequency_bands,
        constraints=MID_CONSTRAINTS,
        subarrays=[
            MidConfigurationCapabilitySet(
                name="AA1",
                receptors=["SKA001", "SKA002", "SKA003", "SKA004"],
                available_bandwidth_hz=800_000_000.0,
                number_pst_beams=1,
                number_fsps=4,
                allowed_channel_width_values_hz=[13440],
            ),
            MidConfigurationCapabilitySet(
                name="AA2",
                receptors=[
                    "SKA001",
                    "SKA002",
                    "SKA003",
                    "SKA004",
                    "SKA005",
                    "SKA006",
                    "SKA007",
                    "SKA008",
                ],  # fmt: skip
                available_bandwidth_hz=800_000_000.0,
                number_pst_beams=1,
                number_fsps=8,
                allowed_channel_width_values_hz=[13440],
            ),
        ],
        spfrx_defaults=MID_DEFAULTS.spfrx_defaults,
    ),
    ska_low=LowConfiguration(
        frequency_band=LOW_FREQUENCY_BAND,
        constraints=LOW_CONSTRAINTS,
        quality_attribute_metrics=ConfigurationLowQualityAttributeMetrics(
            cbf=ConfigurationLowCBFMetrics(processors_ready_percent=100.0)
        ),
        subarrays=[
            LowConfigurationCapabilitySet(
                name="AA1",
                receptors=[345, 346, 347, 348],
                available_bandwidth_hz=75_000_000.0,
                number_pst_beams=1,
                number_fsps=6,
                number_substations=0,
                number_subarray_beams=1,
            ),
            LowConfigurationCapabilitySet(
                name="AA2",
                receptors=[345, 346, 347, 348, 349, 350, 351, 352],
                available_bandwidth_hz=75_000_000.0,
                number_pst_beams=1,
                number_fsps=6,
                number_substations=512,
                number_subarray_beams=8,
            ),
        ],
    ),
)

# The PHT cycle views of tests/tmdata: each cycle with the capability set
# each telescope offers and that telescope's basic capabilities
CYCLE_1_CONFIGURATION = CycleConfiguration(
    observatory_policy=ObservatoryPolicy(
        cycle_number=1,
        cycle_id="TEST_SKAO_2027_Low_AA1_SV",
        type="Science Verification",
        cycle_description="TEST Low AA1 Science Verification",
        cycle_information=CYCLE_1.cycle_information,
        cycle_policies=CYCLE_1.cycle_policies,
        telescope_capabilities=CycleTelescopeCapabilities(ska_mid=None, ska_low="AA1"),
    ),
    capabilities=CycleCapabilities(
        mid=None,
        low=LowCycleCapabilities(
            basic_capabilities=LOW_FREQUENCY_BAND, capability_set=LOW_AA1
        ),
    ),
)

CYCLE_2_CONFIGURATION = CycleConfiguration(
    observatory_policy=ObservatoryPolicy(
        cycle_number=2,
        cycle_id="TEST_SKAO_2027_AA2_Proposal",
        type="Proposal",
        cycle_description="TEST AA2 Proposal",
        cycle_information=CYCLE_2.cycle_information,
        cycle_policies=CYCLE_2.cycle_policies,
        telescope_capabilities=CycleTelescopeCapabilities(ska_mid="AA2", ska_low="AA2"),
    ),
    capabilities=CycleCapabilities(
        mid=MidCycleCapabilities(
            basic_capabilities=MidCycleBasicCapabilities(
                frequency_bands=MID_BASIC_CAPABILITIES.frequency_bands
            ),
            capability_set=MID_AA2,
        ),
        low=LowCycleCapabilities(
            basic_capabilities=LOW_FREQUENCY_BAND, capability_set=LOW_AA2
        ),
    ),
)
