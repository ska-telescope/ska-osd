"""Unit tests for the capabilities, defaults, observatory policy, subarray
template and configuration models.

These use the test copy of the tmdata in tests/tmdata, so changing the real
tmdata doesn't need them updating; test_tmdata_files.py checks the real
files. They cover the models' own logic: the checks across fields, reshaping
the tmdata layout, combining the capabilities and defaults into the
configuration, and validating what the OSD serves.
"""

import json
from datetime import datetime
from pathlib import Path

import pytest
from pydantic import TypeAdapter, ValidationError

from ska_ost_osd.osd.adapters.tmdata.models import (
    CycleFile,
    LowCapabilitiesFile,
    LowDefaultsFile,
    MidCapabilitiesFile,
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
from tests.unit.ska_ost_osd.osd.expected import MID_BASIC_CAPABILITIES

TESTS_TMDATA = Path(__file__).parents[3] / "tmdata"

MID_CAPABILITIES = "ska1_mid/mid_capabilities.json"
LOW_CAPABILITIES = "ska1_low/low_capabilities.json"
MID_DEFAULTS = "ska1_mid/mid_defaults.json"
LOW_DEFAULTS = "ska1_low/low_defaults.json"
CYCLE = "cycles/cycle_1.json"
SUBARRAY_TEMPLATES = "subarray_templates/subarray_template_library.json"


def load(path: str) -> dict:
    with open(TESTS_TMDATA / path, encoding="utf-8") as json_file:
        return json.load(json_file)


class TestOsdOutput:
    """What the OSD serves from the tmdata validates against the models."""

    @pytest.mark.parametrize(
        "model, telescope, path",
        [
            (MidCapabilitiesFile, Telescope.MID, MID_CAPABILITIES),
            (LowCapabilitiesFile, Telescope.LOW, LOW_CAPABILITIES),
        ],
    )
    def test_template_processed_output_validates(
        self, model, telescope, path, tests_tmdata
    ):
        """The OSD's output with subarray templates resolved, as
        ska-oso-services fetches it, validates once the constraints, which
        the OSD no longer returns, are added from the capabilities file."""
        osd_data = get_osd_using_tmdata(
            tests_tmdata, telescope=telescope, process_templates=True
        )
        served = osd_data["capabilities"][telescope.value]
        assert "constraints" not in served

        model.model_validate({**served, "constraints": load(path)["constraints"]})


class TestBreakingChanges:
    """Representative breaking changes to the tmdata files fail validation,
    so test_tmdata_files.py would catch them in the real files."""

    @pytest.mark.parametrize(
        "model, path, break_file",
        [
            (
                MidCapabilitiesFile,
                MID_CAPABILITIES,
                lambda data: data["AA2"].pop("number_fsps"),
            ),
            (
                LowCapabilitiesFile,
                LOW_CAPABILITIES,
                lambda data: data.update(frequency=data.pop("basic_capabilities")),
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
                lambda data: next(iter(data.values())).update(subarray_type="AA9"),
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

    def test_array_assemblies_are_found_by_name(self):
        """Every top-level key matching the array assembly pattern, whether
        an AA name or a telescope-prefixed one such as Low_ITF, becomes a
        capability set, so a new one is picked up and other keys are
        ignored. A capability set need not list subarray templates."""
        data = load(LOW_CAPABILITIES)
        names = {s.name for s in LowCapabilitiesFile.model_validate(data).subarrays}
        data["AA3"] = data["AA2"]
        data["Low_ITF"] = {
            key: value
            for key, value in data["AA2"].items()
            if key != "subarray_templates"
        }
        data["version"] = "1.0"

        capabilities = LowCapabilitiesFile.model_validate(data)

        subarrays = {subarray.name: subarray for subarray in capabilities.subarrays}
        assert set(subarrays) == names | {"AA3", "Low_ITF"}
        assert subarrays["AA1"].receptors == data["AA1"]["number_station_ids"]
        assert subarrays["Low_ITF"].subarray_templates is None

    @pytest.mark.parametrize(
        "model, path, telescope",
        [
            (MidCapabilitiesFile, MID_CAPABILITIES, Telescope.MID),
            (LowCapabilitiesFile, LOW_CAPABILITIES, Telescope.LOW),
        ],
    )
    def test_capability_sets_know_their_telescope(self, model, path, telescope):
        """tmdata doesn't repeat the telescope on each array assembly; the
        capability set models fill it in."""
        capabilities = model.model_validate(load(path))
        assert {cs.telescope for cs in capabilities.subarrays} == {telescope}

    @pytest.mark.parametrize(
        "model, path, capability_set_model",
        [
            (MidCapabilitiesFile, MID_CAPABILITIES, MidCapabilitySet),
            (LowCapabilitiesFile, LOW_CAPABILITIES, LowCapabilitySet),
        ],
    )
    @pytest.mark.parametrize("mode", ["python", "json"])
    def test_capability_set_is_chosen_by_telescope(
        self, model, path, capability_set_model, mode
    ):
        """A serialised capability set reads back as the right capability
        set model, chosen by its telescope."""
        expected = model.model_validate(load(path)).subarrays[0]

        capability_set = TypeAdapter(CapabilitySet).validate_python(
            expected.model_dump(mode=mode)
        )

        assert type(capability_set) is capability_set_model
        assert capability_set == expected

    def test_capability_set_rejects_another_telescope(self):
        data = load(LOW_CAPABILITIES)["AA1"]
        with pytest.raises(ValidationError, match="telescope"):
            LowCapabilitySet.model_validate({"name": "AA1", **data, "telescope": "mid"})

    @pytest.mark.parametrize(
        "model, path",
        [
            (MidCapabilitiesFile, MID_CAPABILITIES),
            (LowCapabilitiesFile, LOW_CAPABILITIES),
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
                MidCapabilitiesFile,
                MID_CAPABILITIES,
                lambda data: data["basic_capabilities"]["receiver_information"][
                    0
                ].update(min_frequency_hz=2e9, max_frequency_hz=1e9),
                "min_frequency_hz must not exceed max_frequency_hz",
            ),
            (
                MidCapabilitiesFile,
                MID_CAPABILITIES,
                lambda data: data["AA2"]["number_dish_ids"].pop(),
                "number_ska_dishes",
            ),
            (
                MidCapabilitiesFile,
                MID_CAPABILITIES,
                lambda data: data["AA2"]["available_receivers"].append("Band_9"),
                "available_receivers",
            ),
            (
                LowCapabilitiesFile,
                LOW_CAPABILITIES,
                lambda data: data["AA2"]["number_station_ids"].pop(),
                "number_stations",
            ),
        ],
        ids=[
            "elevation range",
            "frequency range",
            "dish count",
            "unknown receiver",
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

    def test_telescope_offering_nothing_is_null(self):
        """The PHT UI checks for null, so a telescope missing from the file
        is served as null rather than left out, under the file's keys."""
        data = load(CYCLE)
        data["telescope_capabilities"] = {"Low": "AA2_SV"}

        policy = CycleFile.model_validate(data)

        assert policy.telescope_capabilities.ska_mid is None
        assert policy.telescope_capabilities.ska_low == "AA2_SV"
        served = policy.model_dump(mode="json", by_alias=True)
        assert served["telescope_capabilities"] == {"Mid": None, "Low": "AA2_SV"}
        assert CycleFile.model_validate(policy.model_dump()) == policy

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

    def test_templates_are_named_by_key(self):
        """Each top-level key becomes a template, named after the key."""
        data = load(SUBARRAY_TEMPLATES)

        library = SubarrayTemplateLibraryFile.model_validate(data)

        assert [template.name for template in library.templates] == list(data)

    def test_custom_stations_are_split(self):
        """tmdata's comma-separated stations become a list."""
        data = load(SUBARRAY_TEMPLATES)
        name = next(n for n, t in data.items() if t["subarray_type"] == "custom")

        library = SubarrayTemplateLibraryFile.model_validate(data)

        template = next(t for t in library.templates if t.name == name)
        assert template.custom_stations == data[name]["custom_stations"].split(",")

    @pytest.mark.parametrize(
        "custom, stations, message",
        [
            (True, "", "lists no custom_stations"),
            (False, "SKA001", "only custom templates list custom_stations"),
        ],
        ids=["custom without stations", "stations on a non-custom template"],
    )
    def test_only_custom_templates_list_stations(self, custom, stations, message):
        """Custom templates, and only those, list their stations."""
        data = load(SUBARRAY_TEMPLATES)
        name = next(
            n for n, t in data.items() if (t["subarray_type"] == "custom") == custom
        )
        data[name]["custom_stations"] = stations

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
