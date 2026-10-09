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
from pydantic import ValidationError

from ska_ost_osd.osd.common.constant import Telescope
from ska_ost_osd.osd.models.capabilities import LowCapabilities, MidCapabilities
from ska_ost_osd.osd.models.configuration import (
    Configuration,
    LowConfiguration,
    MidConfiguration,
)
from ska_ost_osd.osd.models.defaults import LowDefaults, MidDefaults
from ska_ost_osd.osd.models.observatory_policies import ObservatoryPolicy
from ska_ost_osd.osd.models.subarray_templates import SubarrayTemplateLibrary
from ska_ost_osd.osd.osd import get_osd_using_tmdata

TESTS_TMDATA = Path(__file__).parents[3] / "tmdata"

MID_CAPABILITIES = "ska1_mid/mid_capabilities.json"
LOW_CAPABILITIES = "ska1_low/low_capabilities.json"
MID_DEFAULTS = "ska1_mid/mid_defaults.json"
LOW_DEFAULTS = "ska1_low/low_defaults.json"
OBSERVATORY_POLICIES = "cycles/cycle_1.json"
SUBARRAY_TEMPLATES = "subarray_templates/subarray_template_library.json"

AVOIDANCE_ANGLES = (
    "sun_avoidance_angle_deg",
    "moon_avoidance_angle_deg",
    "jupiter_avoidance_angle_deg",
)


def load(path: str) -> dict:
    with open(TESTS_TMDATA / path, encoding="utf-8") as json_file:
        return json.load(json_file)


class TestOsdOutput:
    """What the OSD serves from the tmdata validates against the models."""

    @pytest.mark.parametrize(
        "model, telescope, path",
        [
            (MidCapabilities, Telescope.MID, MID_CAPABILITIES),
            (LowCapabilities, Telescope.LOW, LOW_CAPABILITIES),
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
                MidCapabilities,
                MID_CAPABILITIES,
                lambda data: data["AA1"].pop("number_fsps"),
            ),
            (
                LowCapabilities,
                LOW_CAPABILITIES,
                lambda data: data.update(frequency=data.pop("basic_capabilities")),
            ),
            (
                MidDefaults,
                MID_DEFAULTS,
                lambda data: data["defaults"].pop("csp_configuration"),
            ),
            (
                LowDefaults,
                LOW_DEFAULTS,
                lambda data: data["quality_attribute_metrics"]["cbf"].update(
                    processors_ready_percent="all"
                ),
            ),
            (
                ObservatoryPolicy,
                OBSERVATORY_POLICIES,
                lambda data: data.update(cycle=data.pop("cycle_number")),
            ),
            (
                SubarrayTemplateLibrary,
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
        """Every top-level key matching the array assembly pattern becomes a
        subarray, so a new assembly is picked up and other keys are ignored."""
        data = load(LOW_CAPABILITIES)
        names = {s.name for s in LowCapabilities.model_validate(data).subarrays}
        data["AA3"] = data["AA2"]
        data["version"] = "1.0"

        capabilities = LowCapabilities.model_validate(data)

        subarrays = {subarray.name: subarray for subarray in capabilities.subarrays}
        assert set(subarrays) == names | {"AA3"}
        assert subarrays["AA0.5"].receptors == data["AA0.5"]["number_station_ids"]

    @pytest.mark.parametrize(
        "model, path",
        [(MidCapabilities, MID_CAPABILITIES), (LowCapabilities, LOW_CAPABILITIES)],
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

        LowCapabilities.model_validate(data)

    @pytest.mark.parametrize(
        "model, path",
        [(MidCapabilities, MID_CAPABILITIES), (LowCapabilities, LOW_CAPABILITIES)],
    )
    def test_avoidance_angles_not_needed(self, model, path):
        """The avoidance angles now live only in the defaults files, so the
        capabilities files validate without them."""
        data = load(path)
        for angle in AVOIDANCE_ANGLES:
            data["constraints"].pop(angle, None)

        model.model_validate(data)

    @pytest.mark.parametrize(
        "model, path, break_file, message",
        [
            (
                MidCapabilities,
                MID_CAPABILITIES,
                lambda data: data["constraints"].update(
                    min_elevation_deg=90.0, max_elevation_deg=10.0
                ),
                "min_elevation_deg must not exceed max_elevation_deg",
            ),
            (
                MidCapabilities,
                MID_CAPABILITIES,
                lambda data: data["basic_capabilities"]["receiver_information"][
                    0
                ].update(min_frequency_hz=2e9, max_frequency_hz=1e9),
                "min_frequency_hz must not exceed max_frequency_hz",
            ),
            (
                MidCapabilities,
                MID_CAPABILITIES,
                lambda data: data["AA1"]["number_dish_ids"].pop(),
                "number_ska_dishes",
            ),
            (
                MidCapabilities,
                MID_CAPABILITIES,
                lambda data: data["AA2"]["available_receivers"].append("Band_9"),
                "available_receivers",
            ),
            (
                LowCapabilities,
                LOW_CAPABILITIES,
                lambda data: data["AA1"]["number_station_ids"].pop(),
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


class TestDefaults:
    """The defaults models' own logic."""

    def test_noise_diode_options_are_flattened(self):
        """tmdata keys the noise diode options by mode under ``noise_diode``;
        the model lists them, with the default mode alongside."""
        data = load(MID_DEFAULTS)
        noise_diode = data["defaults"]["target"]["dish_spfrx_params"]["noise_diode"]

        target_spfrx = MidDefaults.model_validate(data).spfrx_defaults.target_spfrx

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
            MidDefaults.model_validate(data)

    @pytest.mark.parametrize("old, new", [(False, "off"), (True, "on")])
    def test_boolean_sync_pps_is_read(self, old, new):
        """Releases up to 6.0.9 have a boolean sync_pps; it still reads."""
        data = load(MID_DEFAULTS)
        data["defaults"]["csp_configuration"]["spfrx"]["sync_pps"] = old

        defaults = MidDefaults.model_validate(data)

        assert defaults.spfrx_defaults.csp_spfrx.sync_pps == new

    def test_noise_diode_off_needs_no_option(self):
        """Switching the noise diode off doesn't need an option for it."""
        data = load(MID_DEFAULTS)
        noise_diode = data["defaults"]["target"]["dish_spfrx_params"]["noise_diode"]
        noise_diode["mode"] = "off"
        noise_diode.pop("periodic")

        MidDefaults.model_validate(data)

    @pytest.mark.parametrize(
        "model, path", [(MidDefaults, MID_DEFAULTS), (LowDefaults, LOW_DEFAULTS)]
    )
    def test_serialised_defaults_validate(self, model, path):
        """The models' own output, with the noise diode options already
        flattened, can be read back."""
        defaults = model.model_validate(load(path))
        assert model.model_validate(defaults.model_dump()) == defaults


class TestObservatoryPolicy:
    """The observatory policy model's own logic."""

    def test_cycle_response_policy_validates(self, tests_tmdata):
        """The policy in the OSD's response for the cycle, as the PHT
        endpoints fetch it, validates."""
        cycle = load(OBSERVATORY_POLICIES)["cycle_number"]
        osd_data = get_osd_using_tmdata(
            tests_tmdata, cycle_id=cycle, process_templates=True
        )
        ObservatoryPolicy.model_validate(osd_data["observatory_policy"])

    def test_proposal_dates_are_served_as_the_same_time(self):
        """The dates are parsed, so ``.000Z`` is served as ``Z``, but the
        time is unchanged."""
        data = load(OBSERVATORY_POLICIES)
        policy = ObservatoryPolicy.model_validate(data).model_dump(mode="json")
        for key in ("proposal_open", "proposal_close"):
            assert datetime.fromisoformat(
                policy["cycle_information"][key]
            ) == datetime.fromisoformat(data["cycle_information"][key])

    def test_proposal_dates_need_a_timezone(self):
        data = load(OBSERVATORY_POLICIES)
        data["cycle_information"]["proposal_open"] = "2026-03-27T12:00:00"
        with pytest.raises(ValidationError, match="timezone"):
            ObservatoryPolicy.model_validate(data)

    def test_telescope_offering_nothing_is_null(self):
        """The PHT UI checks for null, so a telescope missing from the file
        is served as null rather than left out, under the file's keys."""
        data = load(OBSERVATORY_POLICIES)
        data["telescope_capabilities"] = {"Low": "AA2_SV"}

        policy = ObservatoryPolicy.model_validate(data)

        assert policy.telescope_capabilities.ska_mid is None
        assert policy.telescope_capabilities.ska_low == "AA2_SV"
        served = policy.model_dump(mode="json", by_alias=True)
        assert served["telescope_capabilities"] == {"Mid": None, "Low": "AA2_SV"}
        assert ObservatoryPolicy.model_validate(policy.model_dump()) == policy

    def test_proposals_must_open_before_they_close(self):
        """A proposal window that closes before it opens is rejected."""
        data = load(OBSERVATORY_POLICIES)
        information = data["cycle_information"]
        information["proposal_open"], information["proposal_close"] = (
            information["proposal_close"],
            information["proposal_open"],
        )
        with pytest.raises(ValidationError, match="proposal_open must be before"):
            ObservatoryPolicy.model_validate(data)


class TestSubarrayTemplates:
    """The subarray template models' own logic."""

    def test_templates_are_named_by_key(self):
        """Each top-level key becomes a template, named after the key."""
        data = load(SUBARRAY_TEMPLATES)

        library = SubarrayTemplateLibrary.model_validate(data)

        assert [template.name for template in library.templates] == list(data)

    def test_custom_stations_are_split(self):
        """tmdata's comma-separated stations become a list."""
        data = load(SUBARRAY_TEMPLATES)
        name = next(n for n, t in data.items() if t["subarray_type"] == "custom")

        library = SubarrayTemplateLibrary.model_validate(data)

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
            SubarrayTemplateLibrary.model_validate(data)


class TestConfiguration:
    """The combined configuration ska-oso-services serves."""

    def test_from_tmdata_combines_capabilities_and_defaults(self, tests_tmdata):
        """Each telescope's configuration combines its capabilities and
        defaults files."""
        configuration = Configuration.from_tmdata(tests_tmdata)

        assert configuration.ska_mid == MidConfiguration.combine(
            MidCapabilities.model_validate(load(MID_CAPABILITIES)),
            MidDefaults.model_validate(load(MID_DEFAULTS)),
        )
        assert configuration.ska_low == LowConfiguration.combine(
            LowCapabilities.model_validate(load(LOW_CAPABILITIES)),
            LowDefaults.model_validate(load(LOW_DEFAULTS)),
        )

    def test_from_tmdata_reads_every_cycle(self, tests_tmdata):
        """The configuration holds the policy of every cycle in the tmdata,
        in cycle order."""
        cycle_files = (TESTS_TMDATA / "cycles").glob("cycle_*.json")
        cycles = sorted(int(path.stem.removeprefix("cycle_")) for path in cycle_files)

        configuration = Configuration.from_tmdata(tests_tmdata)

        assert [p.cycle_number for p in configuration.observatory_policies] == cycles

    def test_odt_keys_come_first_and_unchanged(self, tests_tmdata):
        """/odt/configuration serves ska_mid and ska_low; the observatory
        policies are only added after them."""
        served = Configuration.from_tmdata(tests_tmdata).model_dump(
            mode="json", by_alias=True
        )
        assert list(served) == ["ska_mid", "ska_low", "observatory_policies"]

    def test_all_constraints_served_without_angles_in_capabilities(self):
        """With the angles gone from the capabilities file, the configuration
        still serves all five constraints, the angles from the defaults."""
        capabilities = load(MID_CAPABILITIES)
        for angle in AVOIDANCE_ANGLES:
            capabilities["constraints"].pop(angle, None)
        defaults = load(MID_DEFAULTS)

        configuration = MidConfiguration.combine(
            MidCapabilities.model_validate(capabilities),
            MidDefaults.model_validate(defaults),
        )

        assert configuration.constraints.model_dump() == {
            **{angle: defaults["constraints"][angle] for angle in AVOIDANCE_ANGLES},
            "min_elevation_deg": capabilities["constraints"]["min_elevation_deg"],
            "max_elevation_deg": capabilities["constraints"]["max_elevation_deg"],
        }

    def test_quality_attribute_metrics_come_from_defaults(self):
        """The defaults file is the home of Low's quality attribute metrics;
        the copy in the capabilities file is ignored."""
        capabilities = LowCapabilities.model_validate(load(LOW_CAPABILITIES))
        defaults = load(LOW_DEFAULTS)
        defaults["quality_attribute_metrics"]["cbf"]["processors_ready_percent"] = 50.0

        configuration = LowConfiguration.combine(
            capabilities, LowDefaults.model_validate(defaults)
        )

        assert (
            configuration.quality_attribute_metrics.cbf.processors_ready_percent == 50
        )
        assert configuration.frequency_band == capabilities.frequency_band
        assert configuration.subarrays == capabilities.subarrays

    def test_defaults_avoidance_angles_take_priority(self):
        """The defaults file is the home of the avoidance angles; the
        capabilities file only repeats them for backward compatibility."""
        capabilities = MidCapabilities.model_validate(load(MID_CAPABILITIES))
        defaults = load(MID_DEFAULTS)
        defaults["constraints"]["sun_avoidance_angle_deg"] = 45.0

        configuration = MidConfiguration.combine(
            capabilities, MidDefaults.model_validate(defaults)
        )

        assert configuration.constraints.sun_avoidance_angle_deg == 45.0
        assert (
            configuration.constraints.min_elevation_deg
            == capabilities.constraints.min_elevation_deg
        )

    def test_serialised_configuration_validates(self, tests_tmdata):
        """What ska-oso-services serves can be read back by the same
        models."""
        configuration = Configuration.from_tmdata(tests_tmdata)
        assert Configuration.model_validate(configuration.model_dump()) == configuration
