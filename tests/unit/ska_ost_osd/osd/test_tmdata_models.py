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
    LowArrayAssemblyFile,
    LowBasicCapabilitiesFile,
    LowDefaultsFile,
    LowPolicyFile,
    MidArrayAssemblyFile,
    MidBasicCapabilitiesFile,
    MidDefaultsFile,
    MidPolicyFile,
    SubarrayTemplateLibraryFile,
)
from ska_ost_osd.osd.common.constant import Telescope
from ska_ost_osd.osd.exceptions import (
    Band5bSubbandNotFoundError,
    FrequencyBandNotFoundError,
)
from ska_ost_osd.osd.models.capabilities import (
    Band5bSubband,
    Capabilities,
    LowCapabilities,
    MidCapabilities,
    MidFrequencyBand,
)
from ska_ost_osd.osd.models.constraints import Constraints
from tests.unit.ska_ost_osd.osd.expected import (
    LOW_AA2,
    MID_AA2,
    MID_BASIC_CAPABILITIES,
)

TESTS_TMDATA = Path(__file__).parents[3] / "tmdata"

MID_BASIC_CAPABILITIES_FILE = "telescopes/ska_mid/basic_capabilities.json"
LOW_BASIC_CAPABILITIES_FILE = "telescopes/ska_low/basic_capabilities.json"
MID_ARRAY_ASSEMBLY = "telescopes/ska_mid/array_assemblies/AA2.json"
LOW_ARRAY_ASSEMBLY = "telescopes/ska_low/array_assemblies/AA2.json"
MID_DEFAULTS = "telescopes/ska_mid/defaults.json"
LOW_DEFAULTS = "telescopes/ska_low/defaults.json"
CYCLE = "cycles/TEST_SKAO_2027_Low_AA1_SV.json"
SUBARRAY_TEMPLATES = "telescopes/ska_low/subarray_templates/AA2.json"


def load(path: str) -> dict:
    with open(TESTS_TMDATA / path, encoding="utf-8") as json_file:
        return json.load(json_file)


class TestPolicyFiles:
    @pytest.mark.parametrize(
        "policy, path",
        [(MidPolicyFile, MID_ARRAY_ASSEMBLY), (LowPolicyFile, LOW_ARRAY_ASSEMBLY)],
    )
    def test_can_set_everything_an_array_assembly_sets(self, policy, path):
        """An array assembly file, with a policy in place of its array_assembly,
        validates as a policy and keeps every field: a policy can set
        anything an array assembly does."""
        data = load(path)
        del data["array_assembly"]
        data["policy"] = "cycle_1_science_verification"

        assert policy.model_validate(data).model_dump(exclude_unset=True) == data

    @pytest.mark.parametrize("policy", [MidPolicyFile, LowPolicyFile])
    def test_an_empty_policy_is_valid(self, policy):
        """A policy that sets nothing but its id is valid."""
        data = {"policy": "cycle_1_science_verification"}
        assert policy.model_validate(data).model_dump(exclude_unset=True) == data

    @pytest.mark.parametrize("policy", [MidPolicyFile, LowPolicyFile])
    def test_can_set_part_of_a_group(self, policy):
        """A policy can set one field of a nested group, leaving the rest to
        the array assembly."""
        data = {
            "policy": "cycle_1_science_verification",
            "modes": {"spectral": {"max_zoom_windows": 1}},
        }
        assert policy.model_validate(data).model_dump(exclude_unset=True) == data


class TestBreakingChanges:
    """Representative breaking changes to the tmdata files fail validation,
    so test_tmdata_files.py would catch them in the real files."""

    @pytest.mark.parametrize(
        "model, path, break_file",
        [
            (
                MidArrayAssemblyFile,
                MID_ARRAY_ASSEMBLY,
                lambda data: data.pop("number_fsps"),
            ),
            (
                LowBasicCapabilitiesFile,
                LOW_BASIC_CAPABILITIES_FILE,
                lambda data: data["coarse_channels"].update(
                    width=data["coarse_channels"].pop("width_hz")
                ),
            ),
            (
                MidDefaultsFile,
                MID_DEFAULTS,
                lambda data: data.pop("csp_configuration"),
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
                lambda data: data.update(id=data.pop("cycle_id")),
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
        "expected, capabilities_model",
        [(MID_AA2, MidCapabilities), (LOW_AA2, LowCapabilities)],
    )
    @pytest.mark.parametrize("mode", ["python", "json"])
    def test_capabilities_are_chosen_by_telescope(
        self, expected, capabilities_model, mode
    ):
        """Serialised capabilities read back as the right capabilities
        model, chosen by their telescope."""
        capabilities = TypeAdapter(Capabilities).validate_python(
            expected.model_dump(mode=mode)
        )

        assert type(capabilities) is capabilities_model
        assert capabilities == expected

    def test_capabilities_reject_another_telescope(self):
        data = load(LOW_ARRAY_ASSEMBLY)
        with pytest.raises(ValidationError, match="telescope"):
            LowCapabilities.model_validate(
                {"name": "AA2", **data, "telescope": "ska_mid"}
            )

    @pytest.mark.parametrize(
        "model, path",
        [
            (MidArrayAssemblyFile, MID_ARRAY_ASSEMBLY),
            (LowArrayAssemblyFile, LOW_ARRAY_ASSEMBLY),
        ],
    )
    def test_serialised_capabilities_validate(self, model, path):
        """The models' own output, with the subarrays already collected, can
        be read back."""
        capabilities = model.model_validate(load(path))
        assert model.model_validate(capabilities.model_dump()) == capabilities

    @pytest.mark.parametrize(
        "model, path, break_file, message",
        [
            (
                MidBasicCapabilitiesFile,
                MID_BASIC_CAPABILITIES_FILE,
                lambda data: data["elevation_limits"].update(
                    min_elevation_deg=90.0, max_elevation_deg=10.0
                ),
                "min_elevation_deg must not exceed max_elevation_deg",
            ),
            (
                MidBasicCapabilitiesFile,
                MID_BASIC_CAPABILITIES_FILE,
                lambda data: data["frequency_bands"][0].update(
                    min_frequency_hz=2e9, max_frequency_hz=1e9
                ),
                "min_frequency_hz must not exceed max_frequency_hz",
            ),
            (
                MidArrayAssemblyFile,
                MID_ARRAY_ASSEMBLY,
                lambda data: data["receptors"]["receptor_ids"].pop(),
                "number_ska_dishes",
            ),
            (
                LowArrayAssemblyFile,
                LOW_ARRAY_ASSEMBLY,
                lambda data: data["receptors"]["receptor_ids"].pop(),
                "number_stations",
            ),
            (
                LowArrayAssemblyFile,
                LOW_ARRAY_ASSEMBLY,
                lambda data: data["modes"]["pss"].update(max_beams=1),
                "cbf_modes must list pss",
            ),
            (
                LowArrayAssemblyFile,
                LOW_ARRAY_ASSEMBLY,
                lambda data: data["cbf_modes"].remove("pst"),
                "cbf_modes must list pst",
            ),
            (
                MidArrayAssemblyFile,
                MID_ARRAY_ASSEMBLY,
                lambda data: data["modes"]["pss"].update(max_beams=1),
                "cbf_modes must list pss",
            ),
            (
                MidArrayAssemblyFile,
                MID_ARRAY_ASSEMBLY,
                lambda data: data["cbf_modes"].remove("pst"),
                "cbf_modes must list pst",
            ),
        ],
        ids=[
            "elevation range",
            "frequency range",
            "dish count",
            "station count",
            "pss beams without the pss CBF mode",
            "pst CBF mode without pst beams",
            "Mid pss beams without the pss CBF mode",
            "Mid pst CBF mode without pst beams",
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
        noise_diode = data["target"]["dish_spfrx_params"]["noise_diode"]

        target_spfrx = MidDefaultsFile.model_validate(data).target.dish_spfrx_params

        options = {option.mode: option for option in target_spfrx.noise_diode_options}
        assert target_spfrx.default_noise_diode_mode == noise_diode["mode"]
        assert set(options) == set(noise_diode) - {"mode"}
        assert options["periodic"].period_ms == noise_diode["periodic"]["period_ms"]

    def test_default_noise_diode_mode_needs_an_option(self):
        """The default mode must be one of the options."""
        data = load(MID_DEFAULTS)
        noise_diode = data["target"]["dish_spfrx_params"]["noise_diode"]
        noise_diode["mode"] = "periodic"
        noise_diode.pop("periodic")

        with pytest.raises(ValidationError, match="no matching entry"):
            MidDefaultsFile.model_validate(data)

    @pytest.mark.parametrize("old, new", [(False, "off"), (True, "on")])
    def test_boolean_sync_pps_is_read(self, old, new):
        """Releases up to 6.0.9 have a boolean sync_pps; it still reads."""
        data = load(MID_DEFAULTS)
        data["csp_configuration"]["spfrx"]["sync_pps"] = old

        defaults = MidDefaultsFile.model_validate(data)

        assert defaults.csp_configuration.spfrx.sync_pps == new

    def test_noise_diode_off_needs_no_option(self):
        """Switching the noise diode off doesn't need an option for it."""
        data = load(MID_DEFAULTS)
        noise_diode = data["target"]["dish_spfrx_params"]["noise_diode"]
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

    def test_proposal_dates_are_served_as_the_same_time(self):
        """The dates are parsed, so ``.000Z`` is served as ``Z``, but the
        time is unchanged."""
        data = load(CYCLE)
        policy = CycleFile.model_validate(data).model_dump(mode="json")
        for key in ("opens", "closes"):
            assert datetime.fromisoformat(
                policy["proposal_window"][key]
            ) == datetime.fromisoformat(data["proposal_window"][key])

    def test_cycle_number_can_be_zero(self):
        """Cycle 0 is the first numbered cycle."""
        data = load(CYCLE)
        data["cycle_number"] = 0
        assert CycleFile.model_validate(data).cycle_number == 0

    def test_cycle_number_is_optional(self):
        data = load(CYCLE)
        del data["cycle_number"]
        assert CycleFile.model_validate(data).cycle_number is None

    def test_proposal_dates_need_a_timezone(self):
        data = load(CYCLE)
        data["proposal_window"]["opens"] = "2026-03-27T12:00:00"
        with pytest.raises(ValidationError, match="timezone"):
            CycleFile.model_validate(data)

    def test_telescope_not_offered_is_absent(self):
        """A telescope missing from the file's capabilities is not offered.
        (The PHT view serves it as null: see test_views.py.)"""
        data = load(CYCLE)

        cycle = CycleFile.model_validate(data)

        assert Telescope.SKA_MID not in cycle.capabilities

    def test_proposals_must_open_before_they_close(self):
        """A proposal window that closes before it opens is rejected."""
        data = load(CYCLE)
        window = data["proposal_window"]
        window["opens"], window["closes"] = window["closes"], window["opens"]
        with pytest.raises(ValidationError, match="must open before it closes"):
            CycleFile.model_validate(data)


class TestSubarrayTemplates:
    """The subarray template models' own logic."""

    def test_template_names_are_unique(self):
        """A library listing two templates with the same name is rejected."""
        data = load(SUBARRAY_TEMPLATES)
        data["templates"].append(data["templates"][0])

        with pytest.raises(ValidationError, match="template names are not unique"):
            SubarrayTemplateLibraryFile.model_validate(data)

    @pytest.mark.parametrize(
        "custom, receptor_ids, message",
        [
            (True, [], "lists no receptor_ids"),
            (False, ["SKA001"], "only custom templates list receptor_ids"),
        ],
        ids=["custom without receptors", "receptors on a non-custom template"],
    )
    def test_only_custom_templates_list_receptors(self, custom, receptor_ids, message):
        """Custom templates, and only those, list their receptors."""
        data = load(SUBARRAY_TEMPLATES)
        stored = next(
            t for t in data["templates"] if (t["subarray_type"] == "custom") == custom
        )
        stored["receptor_ids"] = receptor_ids

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
