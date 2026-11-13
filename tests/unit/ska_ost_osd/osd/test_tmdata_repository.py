"""Unit tests for the TMData repository, using the test copy of the tmdata in
tests/tmdata."""

from pathlib import Path

import pytest
from pydantic import ValidationError
from ska_telmodel_client import TMData

from ska_ost_osd.osd.adapters.tmdata import TMDataRepository
from ska_ost_osd.osd.common.constant import Telescope
from ska_ost_osd.osd.exceptions import CapabilitySetNotFoundError, CycleNotFoundError
from ska_ost_osd.osd.models.cycles import Cycle, PolicyType
from tests.unit.ska_ost_osd.osd.expected import (
    CYCLE_1,
    CYCLE_1_FILE,
    CYCLE_2,
    LOW_AA1,
    LOW_AA2,
    LOW_AA2_SV,
    LOW_BASIC_CAPABILITIES,
    LOW_CONSTRAINTS,
    LOW_DEFAULTS,
    LOW_FULL_AA2_TEMPLATE,
    LOW_TEST_AA1_TEMPLATE,
    LOW_TEST_AA2_TEMPLATE,
    MID_AA1,
    MID_AA2,
    MID_BASIC_CAPABILITIES,
    MID_CONSTRAINTS,
    MID_DEFAULTS,
    MID_FULL_AA2_TEMPLATE,
)

TMDATA = Path(__file__).parents[4] / "tmdata"


class TestGetCycleIds:
    def test_returns_sorted_cycle_ids(self, test_tmdata_repository):
        assert test_tmdata_repository.get_cycle_ids() == [
            "TEST_SKAO_2027_AA2_Proposal",
            "TEST_SKAO_2027_Low_AA1_SV",
        ]

    def test_raises_when_cycles_directory_missing(self, empty_tmdata_repository):
        with pytest.raises(FileNotFoundError, match="file not found: cycles"):
            empty_tmdata_repository.get_cycle_ids()

    def test_raises_when_two_cycle_files_share_a_number(self, tmdata_repository_with):
        repository = tmdata_repository_with(
            {
                "cycles/another_cycle_1.json": {
                    **CYCLE_1_FILE.model_dump(mode="json", by_alias=True),
                    "id": "ANOTHER_CYCLE",
                }
            }
        )

        with pytest.raises(ValueError, match="number 1 is in both"):
            repository.get_cycle_ids()

    def test_cycles_without_a_number_are_listed(self, tmdata_repository_with):
        """Cycles without a number, such as science verification before
        Cycle 0, don't clash with each other."""
        unnumbered = CYCLE_1_FILE.model_dump(
            mode="json", by_alias=True, exclude={"number"}
        )
        repository = tmdata_repository_with(
            {
                "cycles/unnumbered_a.json": {**unnumbered, "id": "UNNUMBERED_A"},
                "cycles/unnumbered_b.json": {**unnumbered, "id": "UNNUMBERED_B"},
            }
        )

        assert repository.get_cycle_ids() == [
            "TEST_SKAO_2027_AA2_Proposal",
            "TEST_SKAO_2027_Low_AA1_SV",
            "UNNUMBERED_A",
            "UNNUMBERED_B",
        ]

    def test_raises_when_two_cycle_files_share_an_id(self, tmdata_repository_with):
        repository = tmdata_repository_with(
            {
                "cycles/another_cycle.json": {
                    **CYCLE_1_FILE.model_dump(mode="json", by_alias=True),
                    "number": 3,
                }
            }
        )

        with pytest.raises(ValueError, match="id TEST_SKAO_2027_Low_AA1_SV is in both"):
            repository.get_cycle_ids()


class TestGetCycle:
    @pytest.mark.parametrize(
        "cycle_id, expected",
        [
            ("TEST_SKAO_2027_Low_AA1_SV", CYCLE_1),
            ("TEST_SKAO_2027_AA2_Proposal", CYCLE_2),
        ],
    )
    def test_returns_cycle(self, test_tmdata_repository, cycle_id, expected):
        assert test_tmdata_repository.get_cycle(cycle_id) == expected

    def test_returns_reader_model(self, test_tmdata_repository):
        """The repository returns the reader model, not the storage model it
        is read through."""
        assert (
            type(test_tmdata_repository.get_cycle("TEST_SKAO_2027_Low_AA1_SV")) is Cycle
        )
        assert {type(cycle) for cycle in test_tmdata_repository.get_cycles()} == {Cycle}

    def test_serialises_with_reader_field_names(self, test_tmdata_repository):
        """The PHT's names for the offered telescopes (Mid, Low) belong to
        the PHT view, not to the reader model."""
        served = test_tmdata_repository.get_cycle(
            "TEST_SKAO_2027_Low_AA1_SV"
        ).model_dump(by_alias=True)

        assert served["capabilities"] == {
            "ska_low": {
                "array_assembly": "AA1",
                "policies": {"science_verification": "AA1"},
            }
        }

    def test_raises_for_unknown_cycle(self, test_tmdata_repository):
        with pytest.raises(
            CycleNotFoundError,
            match=r"Cycle NO_SUCH_CYCLE is invalid\. Valid IDs are "
            r"TEST_SKAO_2027_AA2_Proposal, TEST_SKAO_2027_Low_AA1_SV\.",
        ) as excinfo:
            test_tmdata_repository.get_cycle("NO_SUCH_CYCLE")

        assert excinfo.value.cycle_id == "NO_SUCH_CYCLE"
        assert excinfo.value.available_cycle_ids == [
            "TEST_SKAO_2027_AA2_Proposal",
            "TEST_SKAO_2027_Low_AA1_SV",
        ]

    def test_raises_when_cycles_directory_missing(self, empty_tmdata_repository):
        with pytest.raises(FileNotFoundError, match="file not found: cycles"):
            empty_tmdata_repository.get_cycle("TEST_SKAO_2027_Low_AA1_SV")


class TestGetCycles:
    def test_returns_every_cycle_in_id_order(self, test_tmdata_repository):
        assert test_tmdata_repository.get_cycles() == [CYCLE_2, CYCLE_1]

    def test_raises_when_cycles_directory_missing(self, empty_tmdata_repository):
        with pytest.raises(FileNotFoundError, match="file not found: cycles"):
            empty_tmdata_repository.get_cycles()


class TestGetBasicCapabilities:
    @pytest.mark.parametrize(
        "telescope, expected",
        [
            (Telescope.SKA_MID, MID_BASIC_CAPABILITIES),
            (Telescope.SKA_LOW, LOW_BASIC_CAPABILITIES),
        ],
    )
    def test_returns_basic_capabilities(
        self, test_tmdata_repository, telescope, expected
    ):
        assert test_tmdata_repository.get_basic_capabilities(telescope) == expected

    def test_serialises_with_reader_field_names(self, test_tmdata_repository):
        """The PHT's name for Mid's receiver bands (receiver_information)
        belongs to the PHT view, not to the reader model."""
        served = test_tmdata_repository.get_basic_capabilities(
            Telescope.SKA_MID
        ).model_dump(by_alias=True)

        assert list(served) == ["frequency_bands", "elevation_limits"]

    def test_raises_when_file_missing(self, empty_tmdata_repository):
        with pytest.raises(
            FileNotFoundError,
            match="file not found: telescopes/ska_low/basic_capabilities.json",
        ):
            empty_tmdata_repository.get_basic_capabilities(Telescope.SKA_LOW)


class TestGetConstraints:
    @pytest.mark.parametrize(
        "telescope, expected",
        [(Telescope.SKA_MID, MID_CONSTRAINTS), (Telescope.SKA_LOW, LOW_CONSTRAINTS)],
    )
    def test_returns_constraints(self, test_tmdata_repository, telescope, expected):
        assert test_tmdata_repository.get_constraints(telescope) == expected

    def test_raises_when_files_missing(self, empty_tmdata_repository):
        with pytest.raises(
            FileNotFoundError,
            match="file not found: telescopes/ska_mid/basic_capabilities.json",
        ):
            empty_tmdata_repository.get_constraints(Telescope.SKA_MID)


class TestGetDefaults:
    @pytest.mark.parametrize(
        "telescope, expected",
        [(Telescope.SKA_MID, MID_DEFAULTS), (Telescope.SKA_LOW, LOW_DEFAULTS)],
    )
    def test_returns_defaults(self, test_tmdata_repository, telescope, expected):
        assert test_tmdata_repository.get_defaults(telescope) == expected

    def test_raises_when_file_missing(self, empty_tmdata_repository):
        with pytest.raises(
            FileNotFoundError,
            match="file not found: telescopes/ska_mid/defaults.json",
        ):
            empty_tmdata_repository.get_defaults(Telescope.SKA_MID)


class TestGetCapabilitySets:
    @pytest.mark.parametrize(
        "telescope, expected",
        [
            (Telescope.SKA_MID, [MID_AA1, MID_AA2]),
            (Telescope.SKA_LOW, [LOW_AA1, LOW_AA2]),
        ],
    )
    def test_returns_capability_sets_in_file_order(
        self, test_tmdata_repository, telescope, expected
    ):
        assert test_tmdata_repository.get_capability_sets(telescope) == expected

    def test_raises_when_file_missing(self, empty_tmdata_repository):
        with pytest.raises(
            FileNotFoundError,
            match="file not found: telescopes/ska_mid/array_assemblies",
        ):
            empty_tmdata_repository.get_capability_sets(Telescope.SKA_MID)


class TestGetCapabilitySet:
    @pytest.mark.parametrize(
        "telescope, array_assembly, expected",
        [
            (Telescope.SKA_MID, "AA1", MID_AA1),
            (Telescope.SKA_MID, "AA2", MID_AA2),
            (Telescope.SKA_LOW, "AA1", LOW_AA1),
            (Telescope.SKA_LOW, "AA2", LOW_AA2),
        ],
    )
    def test_returns_array_assembly_without_a_policy(
        self, test_tmdata_repository, telescope, array_assembly, expected
    ):
        assert (
            test_tmdata_repository.get_capability_set(telescope, array_assembly)
            == expected
        )

    def test_an_empty_policy_changes_nothing(self, test_tmdata_repository):
        assert (
            test_tmdata_repository.get_capability_set(Telescope.SKA_LOW, "AA2", "AA2")
            == LOW_AA2
        )

    def test_a_policy_changes_only_what_it_sets(self, test_tmdata_repository):
        assert (
            test_tmdata_repository.get_capability_set(
                Telescope.SKA_LOW, "AA2", "AA2_SV"
            )
            == LOW_AA2_SV
        )

    def test_the_result_is_validated(self, tmdata_repository_with):
        """A policy that leaves the result inconsistent is rejected: here pst
        is dropped from cbf_modes but the pst beams are kept."""
        repository = tmdata_repository_with(
            {
                "telescopes/ska_low/policies/bad.json": {
                    "id": "bad",
                    "cbf_modes": ["vis"],
                }
            }
        )
        with pytest.raises(ValidationError, match="cbf_modes must list pst"):
            repository.get_capability_set(Telescope.SKA_LOW, "AA2", "bad")

    def test_raises_for_unknown_policy(self, test_tmdata_repository):
        with pytest.raises(
            FileNotFoundError, match="no policy file in .* has id NO_SUCH_POLICY"
        ):
            test_tmdata_repository.get_capability_set(
                Telescope.SKA_LOW, "AA2", "NO_SUCH_POLICY"
            )

    def test_low_aa2_with_the_aa2_sv_policy_is_the_aa2_sv_capability_set(self):
        """In the real tmdata, the AA2_SV policy applied to Low AA2 gives what
        the AA2_SV capability set file says."""
        repository = TMDataRepository(TMData([f"file://{TMDATA}"]))
        assert repository.get_capability_set(
            Telescope.SKA_LOW, "AA2", "AA2_SV"
        ) == repository.get_capability_set(Telescope.SKA_LOW, "AA2_SV")

    def test_raises_for_unknown_name(self, test_tmdata_repository):
        with pytest.raises(
            CapabilitySetNotFoundError,
            match=(
                r"Capability set AA3 is invalid for telescope ska_mid\. "
                r"Valid capability sets are AA1, AA2\."
            ),
        ) as excinfo:
            test_tmdata_repository.get_capability_set(Telescope.SKA_MID, "AA3")

        assert excinfo.value.telescope == Telescope.SKA_MID
        assert excinfo.value.name == "AA3"
        assert excinfo.value.available_names == ["AA1", "AA2"]

    def test_raises_when_file_missing(self, empty_tmdata_repository):
        with pytest.raises(
            FileNotFoundError,
            match="file not found: telescopes/ska_low/array_assemblies",
        ):
            empty_tmdata_repository.get_capability_set(Telescope.SKA_LOW, "AA1")


class TestGetSubarrayTemplates:
    @pytest.mark.parametrize(
        "telescope, capability_set, expected",
        [
            (Telescope.SKA_MID, "AA1", []),
            (Telescope.SKA_MID, "AA2", [MID_FULL_AA2_TEMPLATE]),
            (Telescope.SKA_LOW, "AA1", [LOW_TEST_AA1_TEMPLATE]),
            (Telescope.SKA_LOW, "AA2", [LOW_FULL_AA2_TEMPLATE, LOW_TEST_AA2_TEMPLATE]),
        ],
        ids=[
            "no template",
            "full template only",
            "subset template only",
            "full and subset templates",
        ],
    )
    def test_returns_subarray_templates(
        self, test_tmdata_repository, telescope, capability_set, expected
    ):
        """The pattern *_AA2 matches templates of both telescopes; only the
        capability set's own telescope's templates are returned."""
        assert (
            test_tmdata_repository.get_subarray_templates(telescope, capability_set)
            == expected
        )

    def test_raises_for_unknown_capability_set(self, test_tmdata_repository):
        with pytest.raises(CapabilitySetNotFoundError):
            test_tmdata_repository.get_subarray_templates(Telescope.SKA_MID, "AA3")


class TestGetCycleCapabilitySets:
    @pytest.mark.parametrize(
        "cycle_id, expected",
        [
            (
                "TEST_SKAO_2027_Low_AA1_SV",
                {Telescope.SKA_LOW: {PolicyType.SCIENCE_VERIFICATION: LOW_AA1}},
            ),
            (
                "TEST_SKAO_2027_AA2_Proposal",
                {
                    Telescope.SKA_MID: {PolicyType.STANDARD_OPERATIONS: MID_AA2},
                    Telescope.SKA_LOW: {PolicyType.STANDARD_OPERATIONS: LOW_AA2},
                },
            ),
        ],
        ids=["low only", "mid and low"],
    )
    def test_returns_capability_sets_offered(
        self, test_tmdata_repository, cycle_id, expected
    ):
        assert test_tmdata_repository.get_cycle_capability_sets(cycle_id) == expected

    def test_raises_for_unknown_cycle(self, test_tmdata_repository):
        with pytest.raises(CycleNotFoundError):
            test_tmdata_repository.get_cycle_capability_sets("NO_SUCH_CYCLE")

    @pytest.mark.parametrize(
        "array_assembly, policy_id, error, message",
        [
            ("AA3", "AA1", CapabilitySetNotFoundError, "Capability set AA3"),
            ("AA1", "AA3", FileNotFoundError, "no policy file in .* has id AA3"),
        ],
        ids=["unknown array assembly", "unknown policy"],
    )
    def test_raises_when_cycle_names_unknown_array_assembly_or_policy(
        self, tmdata_repository_with, array_assembly, policy_id, error, message
    ):
        """An array assembly or policy the cycle names but that doesn't exist
        is an error rather than being skipped."""
        repository = tmdata_repository_with(
            {
                "cycles/TEST_SKAO_2027_Low_AA1_SV.json": {
                    **CYCLE_1_FILE.model_dump(mode="json", by_alias=True),
                    "capabilities": {
                        "ska_low": {
                            "array_assembly": array_assembly,
                            "policies": {"science_verification": policy_id},
                        }
                    },
                }
            }
        )

        with pytest.raises(error, match=message):
            repository.get_cycle_capability_sets("TEST_SKAO_2027_Low_AA1_SV")
