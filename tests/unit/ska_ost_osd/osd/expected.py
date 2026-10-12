"""The models expected from the test copy of the tmdata in tests/tmdata,
written out field by field so the queries are checked against the files
rather than against each other."""

from datetime import datetime, timezone

from ska_ost_osd.osd.models.capabilities import (
    Band5bSubband,
    ElevationConstraints,
    LowBasicCapabilities,
    LowCapabilities,
    LowCapabilitySet,
    LowCBFMode,
    MidBasicCapabilities,
    MidCapabilities,
    MidCapabilitySet,
    MidCBFMode,
    MidFrequencyBand,
)
from ska_ost_osd.osd.models.configuration import Constraints
from ska_ost_osd.osd.models.defaults import (
    AvoidanceConstraints,
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
from ska_ost_osd.osd.models.observatory_policies import (
    CycleID,
    CycleInformation,
    CyclePolicies,
    ObservatoryPolicy,
    TelescopeCapabilities,
)

# tests/tmdata/cycles/cycle_1.json
CYCLE_1 = ObservatoryPolicy(
    cycle_number=CycleID(1),
    cycle_id="TEST_SKAO_2027_Low_AA0.5_SV",
    type="Science Verification",
    cycle_description="TEST Low AA0.5 Science Verification",
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
    telescope_capabilities=TelescopeCapabilities(ska_mid=None, ska_low="AA0.5"),
)

# tests/tmdata/cycles/cycle_2.json
CYCLE_2 = ObservatoryPolicy(
    cycle_number=CycleID(2),
    cycle_id="TEST_SKAO_2027_AA1_Proposal",
    type="Proposal",
    cycle_description="TEST AA1 Proposal",
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
    telescope_capabilities=TelescopeCapabilities(ska_mid="AA1", ska_low="AA1"),
)

# tests/tmdata/ska1_mid/mid_capabilities.json
MID_AA05 = MidCapabilitySet(
    name="AA0.5",
    receptors=["SKA001", "SKA036", "SKA077", "SKA100"],
    available_bandwidth_hz=800_000_000,
    number_pst_beams=1,
    number_fsps=4,
    max_baseline_km=1.5,
    number_zoom_windows=0,
    number_zoom_channels=0,
    number_pss_beams=0,
    ps_beam_bandwidth_hz=400_000_000,
    subarray_templates=["*_AA0.5"],
    allowed_channel_width_values_hz=[13440],
    allowed_channel_count_range_min=[1],
    allowed_channel_count_range_max=[58982],
    available_receivers=["Band_1", "Band_2", "Band_5b"],
    cbf_modes=[MidCBFMode.CORRELATION, MidCBFMode.PST],
    number_ska_dishes=4,
    number_meerkat_dishes=0,
    number_meerkatplus_dishes=0,
)

MID_AA1 = MidCapabilitySet(
    name="AA1",
    receptors=[
        "SKA036",
        "SKA040",
        "SKA045",
        "SKA046",
        "SKA048",
        "SKA077",
        "SKA081",
        "SKA101",
    ],  # fmt: skip
    available_bandwidth_hz=800_000_000,
    number_pst_beams=1,
    number_fsps=8,
    max_baseline_km=1.5,
    number_zoom_windows=0,
    number_zoom_channels=0,
    number_pss_beams=0,
    ps_beam_bandwidth_hz=400_000_000,
    subarray_templates=["*_AA1"],
    allowed_channel_width_values_hz=[13440],
    allowed_channel_count_range_min=[1],
    allowed_channel_count_range_max=[58982],
    available_receivers=["Band_1", "Band_2", "Band_5a", "Band_5b"],
    cbf_modes=[MidCBFMode.CORRELATION, MidCBFMode.PST],
    number_ska_dishes=8,
    number_meerkat_dishes=0,
    number_meerkatplus_dishes=0,
)

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
)

MID_CAPABILITIES = MidCapabilities(
    constraints=ElevationConstraints(min_elevation_deg=15.0, max_elevation_deg=90.0),
    basic_capabilities=MID_BASIC_CAPABILITIES,
    subarrays=[MID_AA05, MID_AA1],
)

# tests/tmdata/ska1_low/low_capabilities.json
LOW_AA05 = LowCapabilitySet(
    name="AA0.5",
    receptors=[345, 350, 352, 431],
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
    subarray_templates=["*_AA0.5"],
    allowed_zoom_factors=[0],
)

LOW_AA1 = LowCapabilitySet(
    name="AA1",
    receptors=[
        345,
        346,
        347,
        348,
        349,
        350,
        351,
        352,
        353,
        354,
        429,
        430,
        431,
        432,
        433,
        434,
    ],  # fmt: skip
    number_stations=16,
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
    subarray_templates=["*_AA1"],
    allowed_zoom_factors=[1, 2, 4, 8],
)

LOW_BASIC_CAPABILITIES = LowBasicCapabilities(
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

LOW_CAPABILITIES = LowCapabilities(
    constraints=ElevationConstraints(min_elevation_deg=45.0, max_elevation_deg=90.0),
    basic_capabilities=LOW_BASIC_CAPABILITIES,
    subarrays=[LOW_AA05, LOW_AA1],
)

# tests/tmdata/ska1_mid/mid_defaults.json
MID_DEFAULTS = MidDefaults(
    constraints=AvoidanceConstraints(
        sun_avoidance_angle_deg=30.0,
        moon_avoidance_angle_deg=10.0,
        jupiter_avoidance_angle_deg=10.0,
    ),
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

# tests/tmdata/ska1_low/low_defaults.json
LOW_DEFAULTS = LowDefaults(
    constraints=AvoidanceConstraints(
        sun_avoidance_angle_deg=30.0,
        moon_avoidance_angle_deg=10.0,
        jupiter_avoidance_angle_deg=10.0,
    ),
    quality_attribute_metrics=LowQualityAttributeMetrics(
        cbf=LowCBFMetrics(processors_ready_percent=100, alveo_configured_percent=100)
    ),
)

# Elevation limits from tests/tmdata/ska1_mid/mid_capabilities.json and
# avoidance angles from mid_defaults.json
MID_CONSTRAINTS = Constraints(
    min_elevation_deg=15.0,
    max_elevation_deg=90.0,
    sun_avoidance_angle_deg=30.0,
    moon_avoidance_angle_deg=10.0,
    jupiter_avoidance_angle_deg=10.0,
)

# Elevation limits from tests/tmdata/ska1_low/low_capabilities.json and
# avoidance angles from low_defaults.json
LOW_CONSTRAINTS = Constraints(
    min_elevation_deg=45.0,
    max_elevation_deg=90.0,
    sun_avoidance_angle_deg=30.0,
    moon_avoidance_angle_deg=10.0,
    jupiter_avoidance_angle_deg=10.0,
)
