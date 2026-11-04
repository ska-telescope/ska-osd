"""Unit tests for the capabilities, defaults, cycle, subarray template and
constraints models: the storage models and the reader models.

These use the test copy of the tmdata in tests/tmdata, so changing the real
tmdata doesn't need them updating; test_tmdata_files.py checks the real
files. They cover the models' own logic: the checks across fields, reshaping
the tmdata layout, and validating what the legacy OSD API serves.
"""

import json
from datetime import datetime
from pathlib import Path

import pytest
from pydantic import TypeAdapter, ValidationError

from ska_ost_osd.osd.adapters.tmdata.models import (
    CycleFile,
    LowBasicCapabilitiesFile,
    LowCapabilitiesFile,
    LowCapabilitySetFile,
    LowDefaultsFile,
    MidBasicCapabilitiesFile,
    MidCapabilitiesFile,
    MidCapabilitySetFile,
    MidDefaultsFile,
    SubarrayTemplateLibraryFile,
)
from ska_ost_osd.osd.common.constant import Telescope
from ska_ost_osd.osd.exceptions import (
    Band5bSubbandNotFoundError,
    FrequencyBandNotFoundError,
)
from ska_ost_osd.osd.models.capabilities import (
    Band5bSubband,
    CapabilitySet,
    LowCapabilitySet,
    MidCapabilitySet,
    MidFrequencyBand,
)
from ska_ost_osd.osd.models.constraints import Constraints
from ska_ost_osd.osd.osd import get_osd_using_tmdata
from tests.unit.ska_ost_osd.osd.expected import (
    LOW_AA2,
    MID_AA2,
    MID_BASIC_CAPABILITIES,
)

TESTS_TMDATA = Path(__file__).parents[3] / "tmdata"

MID_CAPABILITIES = "ska1_mid/mid_capabilities.json"
LOW_CAPABILITIES = "ska1_low/low_capabilities.json"
MID_BASIC_CAPABILITIES_FILE = "ska1_mid/basic_capabilities.json"
LOW_BASIC_CAPABILITIES_FILE = "ska1_low/basic_capabilities.json"
MID_CAPABILITY_SET = "ska1_mid/capabilities/AA2.json"
LOW_CAPABILITY_SET = "ska1_low/capabilities/AA2.json"
MID_DEFAULTS = "ska1_mid/mid_defaults.json"
LOW_DEFAULTS = "ska1_low/low_defaults.json"
CYCLE = "cycles/cycle_1.json"
SUBARRAY_TEMPLATES = "ska1_low/subarray_templates/AA2.json"


def load(path: str) -> dict:
    with open(TESTS_TMDATA / path, encoding="utf-8") as json_file:
        return json.load(json_file)


class TestOsdOutput:
    """What the OSD serves from the tmdata validates against the models."""

    @pytest.mark.parametrize(
        "model, telescope, key",
        [
            (MidCapabilitySet, Telescope.SKA_MID, "mid"),
            (LowCapabilitySet, Telescope.SKA_LOW, "low"),
        ],
    )
    def test_template_processed_output_validates(
        self, model, telescope, key, tests_tmdata
    ):
        """The capability sets in the OSD's output with subarray templates
        resolved, as ska-oso-services fetches it, validate."""
        osd_data = get_osd_using_tmdata(
            tests_tmdata, telescope=telescope, process_templates=True
        )
        served = osd_data["capabilities"][key]
        assert "constraints" not in served

        for name, capability_set in served.items():
            if name != "basic_capabilities":
                model.model_validate({"name": name, **capability_set})


class TestBreakingChanges:
    """Representative breaking changes to the tmdata files fail validation,
    so test_tmdata_files.py would catch them in the real files."""

    @pytest.mark.parametrize(
        "model, path, break_file",
        [
            (
                MidCapabilitySetFile,
                MID_CAPABILITY_SET,
                lambda data: data.pop("number_fsps"),
            ),
            (
                LowBasicCapabilitiesFile,
                LOW_BASIC_CAPABILITIES_FILE,
                lambda data: data.update(
                    coarse_channel_width=data.pop("coarse_channel_width_hz")
                ),
            ),
            (
                MidDefaultsFile,
                MID_DEFAULTS,
                lambda data: data["defaults"].pop("csp_configuration"),
            ),
            (
                LowDefaultsFile,
                LOW_DEFAULTS,
                lambda data: data["quality_attribute_metrics"]["cbf"].update(
                    processors_ready_percent="all"
                ),
            ),
            (
                CycleFile,
                CYCLE,
                lambda data: data.update(cycle=data.pop("cycle_number")),
            ),
            (
                SubarrayTemplateLibraryFile,
                SUBARRAY_TEMPLATES,
                lambda data: data["templates"][0].update(subarray_type="AA9"),
            ),
        ],
        ids=[
            "field removed",
            "key renamed",
            "section removed",
            "type changed",
            "policy key renamed",
            "unknown template type",
        ],
    )
    def test_breaking_change_fails_validation(self, model, path, break_file):
        """The models reject the changed file."""
        data = load(path)
        break_file(data)
        with pytest.raises(ValidationError):
            model.model_validate(data)


class TestCapabilities:
    """The capabilities models' own logic."""

    @pytest.mark.parametrize(
        "expected, capability_set_model",
        [(MID_AA2, MidCapabilitySet), (LOW_AA2, LowCapabilitySet)],
    )
    @pytest.mark.parametrize("mode", ["python", "json"])
    def test_capability_set_is_chosen_by_telescope(
        self, expected, capability_set_model, mode
    ):
        """A serialised capability set reads back as the right capability
        set model, chosen by its telescope."""
        capability_set = TypeAdapter(CapabilitySet).validate_python(
            expected.model_dump(mode=mode)
        )

        assert type(capability_set) is capability_set_model
        assert capability_set == expected

    def test_capability_set_rejects_another_telescope(self):
        data = load(LOW_CAPABILITY_SET)
        with pytest.raises(ValidationError, match="telescope"):
            LowCapabilitySet.model_validate(
                {"name": "AA2", **data, "telescope": "ska_mid"}
            )

    @pytest.mark.parametrize(
        "model, path",
        [
            (MidCapabilitiesFile, MID_CAPABILITIES),
            (LowCapabilitiesFile, LOW_CAPABILITIES),
            (MidCapabilitySetFile, MID_CAPABILITY_SET),
            (LowCapabilitySetFile, LOW_CAPABILITY_SET),
        ],
    )
    def test_serialised_capabilities_validate(self, model, path):
        """The models' own output, with the subarrays already collected, can
        be read back."""
        capabilities = model.model_validate(load(path))
        assert model.model_validate(capabilities.model_dump()) == capabilities

    def test_quality_attribute_metrics_not_needed(self):
        """Low's quality attribute metrics now live only in the defaults
        file, so the capabilities file validates without them."""
        data = load(LOW_CAPABILITIES)
        data.pop("quality_attribute_metrics", None)

        LowCapabilitiesFile.model_validate(data)

    @pytest.mark.parametrize(
        "model, path, break_file, message",
        [
            (
                MidCapabilitiesFile,
                MID_CAPABILITIES,
                lambda data: data["constraints"].update(
                    min_elevation_deg=90.0, max_elevation_deg=10.0
                ),
                "min_elevation_deg must not exceed max_elevation_deg",
            ),
            (
                MidBasicCapabilitiesFile,
                MID_BASIC_CAPABILITIES_FILE,
                lambda data: data["receiver_information"][0].update(
                    min_frequency_hz=2e9, max_frequency_hz=1e9
                ),
                "min_frequency_hz must not exceed max_frequency_hz",
            ),
            (
                MidCapabilitySetFile,
                MID_CAPABILITY_SET,
                lambda data: data["number_dish_ids"].pop(),
                "number_ska_dishes",
            ),
            (
                LowCapabilitySetFile,
                LOW_CAPABILITY_SET,
                lambda data: data["number_station_ids"].pop(),
                "number_stations",
            ),
        ],
        ids=[
            "elevation range",
            "frequency range",
            "dish count",
            "station count",
        ],
    )
    def test_consistency_checks(self, model, path, break_file, message):
        """The checks across fields catch inconsistent tmdata."""
        data = load(path)
        break_file(data)
        with pytest.raises(ValidationError, match=message):
            model.model_validate(data)


class TestMidBasicCapabilities:
    """Looking up Mid's receiver bands and Band 5b's sub-bands by key."""

    def test_get_frequency_band(self):
        assert MID_BASIC_CAPABILITIES.get_frequency_band("Band_2") == (
            MidFrequencyBand(
                rx_id="Band_2",
                min_frequency_hz=950_000_000,
                max_frequency_hz=1_760_000_000,
            )
        )

    def test_get_frequency_band_raises_for_unknown_rx_id(self):
        with pytest.raises(
            FrequencyBandNotFoundError,
            match=(
                r"Frequency band Band_9 is invalid\. Valid frequency bands are "
                r"Band_1, Band_2, Band_3, Band_4, Band_5a, Band_5b\."
            ),
        ) as excinfo:
            MID_BASIC_CAPABILITIES.get_frequency_band("Band_9")

        assert excinfo.value.rx_id == "Band_9"
        assert excinfo.value.available_rx_ids == [
            "Band_1", "Band_2", "Band_3", "Band_4", "Band_5a", "Band_5b",
        ]  # fmt: skip

    def test_get_band5b_subband(self):
        band = MID_BASIC_CAPABILITIES.get_frequency_band("Band_5b")

        assert band.get_band5b_subband(2) == Band5bSubband(
            sub_band=2,
            min_frequency_hz=12_810_000_000,
            max_frequency_hz=13_510_000_000,
            lo_frequency_hz=13_860_000_000,
            sideband="low",
        )

    def test_get_band5b_subband_raises_for_unknown_sub_band(self):
        band = MID_BASIC_CAPABILITIES.get_frequency_band("Band_5b")

        with pytest.raises(
            Band5bSubbandNotFoundError,
            match=(
                r"Sub-band 4 is invalid for Band_5b\. Valid sub-bands are 1, 2, 3\."
            ),
        ) as excinfo:
            band.get_band5b_subband(4)

        assert excinfo.value.rx_id == "Band_5b"
        assert excinfo.value.sub_band == 4
        assert excinfo.value.available_sub_bands == [1, 2, 3]

    def test_get_band5b_subband_raises_for_band_without_sub_bands(self):
        band = MID_BASIC_CAPABILITIES.get_frequency_band("Band_1")

        with pytest.raises(
            Band5bSubbandNotFoundError,
            match=r"Sub-band 1 is invalid for Band_1\. Valid sub-bands are none\.",
        ):
            band.get_band5b_subband(1)


class TestDefaults:
    """The defaults models' own logic."""

    def test_noise_diode_options_are_flattened(self):
        """tmdata keys the noise diode options by mode under ``noise_diode``;
        the model lists them, with the default mode alongside."""
        data = load(MID_DEFAULTS)
        noise_diode = data["defaults"]["target"]["dish_spfrx_params"]["noise_diode"]

        target_spfrx = MidDefaultsFile.model_validate(data).spfrx_defaults.target_spfrx

        options = {option.mode: option for option in target_spfrx.noise_diode_options}
        assert target_spfrx.default_noise_diode_mode == noise_diode["mode"]
        assert set(options) == set(noise_diode) - {"mode"}
        assert options["periodic"].period_ms == noise_diode["periodic"]["period_ms"]

    def test_default_noise_diode_mode_needs_an_option(self):
        """The default mode must be one of the options."""
        data = load(MID_DEFAULTS)
        noise_diode = data["defaults"]["target"]["dish_spfrx_params"]["noise_diode"]
        noise_diode["mode"] = "periodic"
        noise_diode.pop("periodic")

        with pytest.raises(ValidationError, match="no matching entry"):
            MidDefaultsFile.model_validate(data)

    @pytest.mark.parametrize("old, new", [(False, "off"), (True, "on")])
    def test_boolean_sync_pps_is_read(self, old, new):
        """Releases up to 6.0.9 have a boolean sync_pps; it still reads."""
        data = load(MID_DEFAULTS)
        data["defaults"]["csp_configuration"]["spfrx"]["sync_pps"] = old

        defaults = MidDefaultsFile.model_validate(data)

        assert defaults.spfrx_defaults.csp_spfrx.sync_pps == new

    def test_noise_diode_off_needs_no_option(self):
        """Switching the noise diode off doesn't need an option for it."""
        data = load(MID_DEFAULTS)
        noise_diode = data["defaults"]["target"]["dish_spfrx_params"]["noise_diode"]
        noise_diode["mode"] = "off"
        noise_diode.pop("periodic")

        MidDefaultsFile.model_validate(data)

    @pytest.mark.parametrize(
        "model, path",
        [(MidDefaultsFile, MID_DEFAULTS), (LowDefaultsFile, LOW_DEFAULTS)],
    )
    def test_serialised_defaults_validate(self, model, path):
        """The models' own output, with the noise diode options already
        flattened, can be read back."""
        defaults = model.model_validate(load(path))
        assert model.model_validate(defaults.model_dump()) == defaults


class TestCycleFile:
    """The cycle file model's own logic."""

    def test_cycle_response_policy_validates(self, tests_tmdata):
        """The policy in the OSD's response for the cycle, as the PHT
        endpoints fetch it, validates."""
        cycle = load(CYCLE)["cycle_number"]
        osd_data = get_osd_using_tmdata(
            tests_tmdata, cycle_id=cycle, process_templates=True
        )
        CycleFile.model_validate(osd_data["observatory_policy"])

    def test_proposal_dates_are_served_as_the_same_time(self):
        """The dates are parsed, so ``.000Z`` is served as ``Z``, but the
        time is unchanged."""
        data = load(CYCLE)
        policy = CycleFile.model_validate(data).model_dump(mode="json")
        for key in ("proposal_open", "proposal_close"):
            assert datetime.fromisoformat(
                policy["cycle_information"][key]
            ) == datetime.fromisoformat(data["cycle_information"][key])

    def test_proposal_dates_need_a_timezone(self):
        data = load(CYCLE)
        data["cycle_information"]["proposal_open"] = "2026-03-27T12:00:00"
        with pytest.raises(ValidationError, match="timezone"):
            CycleFile.model_validate(data)

    def test_telescope_offering_nothing_is_none(self):
        """A telescope missing from the file's telescope_capabilities is read
        as None. (The PHT view serves it as null: see test_views.py.)"""
        data = load(CYCLE)
        data["telescope_capabilities"] = {"Low": "AA2_SV"}

        policy = CycleFile.model_validate(data)

        assert policy.telescope_capabilities.ska_mid is None
        assert policy.telescope_capabilities.ska_low == "AA2_SV"

    def test_proposals_must_open_before_they_close(self):
        """A proposal window that closes before it opens is rejected."""
        data = load(CYCLE)
        information = data["cycle_information"]
        information["proposal_open"], information["proposal_close"] = (
            information["proposal_close"],
            information["proposal_open"],
        )
        with pytest.raises(ValidationError, match="proposal_open must be before"):
            CycleFile.model_validate(data)


class TestSubarrayTemplates:
    """The subarray template models' own logic."""

    @pytest.mark.parametrize(
        "custom, stations, message",
        [
            (True, [], "lists no custom_stations"),
            (False, ["SKA001"], "only custom templates list custom_stations"),
        ],
        ids=["custom without stations", "stations on a non-custom template"],
    )
    def test_only_custom_templates_list_stations(self, custom, stations, message):
        """Custom templates, and only those, list their stations."""
        data = load(SUBARRAY_TEMPLATES)
        stored = next(
            t for t in data["templates"] if (t["subarray_type"] == "custom") == custom
        )
        stored["custom_stations"] = stations

        with pytest.raises(ValidationError, match=message):
            SubarrayTemplateLibraryFile.model_validate(data)


class TestConstraints:
    """Constraints validates its own fields, independently of the storage
    models it is built from."""

    VALID = {
        "min_elevation_deg": 15.0,
        "max_elevation_deg": 90.0,
        "sun_avoidance_angle_deg": 45.0,
        "moon_avoidance_angle_deg": 5.0,
        "jupiter_avoidance_angle_deg": 5.0,
    }

    def test_accepts_valid_constraints(self):
        assert Constraints(**self.VALID).model_dump() == self.VALID

    @pytest.mark.parametrize(
        "update, message",
        [
            (
                {"min_elevation_deg": 90.0, "max_elevation_deg": 10.0},
                "min_elevation_deg must not exceed max_elevation_deg",
            ),
            ({"min_elevation_deg": -1.0}, "greater than or equal to 0"),
            ({"max_elevation_deg": 91.0}, "less than or equal to 90"),
        ],
        ids=["elevation range", "below horizon", "above zenith"],
    )
    def test_rejects_invalid_elevations(self, update, message):
        with pytest.raises(ValidationError, match=message):
            Constraints(**{**self.VALID, **update})

    @pytest.mark.parametrize("field", list(VALID))
    def test_requires_every_field(self, field):
        data = {key: value for key, value in self.VALID.items() if key != field}

        with pytest.raises(ValidationError, match=field):
            Constraints(**data)
