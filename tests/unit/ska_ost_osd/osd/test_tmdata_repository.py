"""Unit tests for the TMData repository, using the test copy of the tmdata in
tests/tmdata."""

import pytest

from ska_ost_osd.osd import queries
from ska_ost_osd.osd.common.constant import Telescope
from ska_ost_osd.osd.exceptions import CapabilitySetNotFoundError, CycleNotFoundError
from ska_ost_osd.osd.models.cycles import Cycle, CycleID
from tests.unit.ska_ost_osd.osd.expected import (
    CYCLE_1,
    CYCLE_2,
    LOW_AA1,
    LOW_AA2,
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


class TestGetCycleIds:
    def test_returns_sorted_cycle_ids(self, test_tmdata_repository):
        assert test_tmdata_repository.get_cycle_ids() == [CycleID(1), CycleID(2)]

    def test_raises_when_cycles_directory_missing(self, empty_tmdata_repository):
        with pytest.raises(FileNotFoundError, match="file not found: cycles"):
            empty_tmdata_repository.get_cycle_ids()


class TestGetCycle:
    @pytest.mark.parametrize(
        "cycle_id, expected", [(CycleID(1), CYCLE_1), (CycleID(2), CYCLE_2)]
    )
    def test_returns_cycle(self, test_tmdata_repository, cycle_id, expected):
        assert test_tmdata_repository.get_cycle(cycle_id) == expected

    def test_returns_reader_model(self, test_tmdata_repository):
        """The repository returns the reader model, not the storage model it
        is read through."""
        assert type(test_tmdata_repository.get_cycle(CycleID(1))) is Cycle
        assert {type(cycle) for cycle in test_tmdata_repository.get_cycles()} == {Cycle}

    def test_raises_for_unknown_cycle(self, test_tmdata_repository):
        with pytest.raises(
            CycleNotFoundError, match=r"Cycle 3 is invalid\. Valid IDs are 1,2\."
        ) as excinfo:
            test_tmdata_repository.get_cycle(CycleID(3))

        assert excinfo.value.cycle_id == 3
        assert excinfo.value.available_cycle_ids == [1, 2]

    def test_raises_when_cycles_directory_missing(self, empty_tmdata_repository):
        with pytest.raises(FileNotFoundError, match="file not found: cycles"):
            empty_tmdata_repository.get_cycle(CycleID(1))


class TestGetCycles:
    def test_returns_every_cycle_in_id_order(self, test_tmdata_repository):
        assert test_tmdata_repository.get_cycles() == [CYCLE_1, CYCLE_2]

    def test_raises_when_cycles_directory_missing(self, empty_tmdata_repository):
        with pytest.raises(FileNotFoundError, match="file not found: cycles"):
            empty_tmdata_repository.get_cycles()


class TestGetBasicCapabilities:
    @pytest.mark.parametrize(
        "telescope, expected",
        [
            (Telescope.MID, MID_BASIC_CAPABILITIES),
            (Telescope.LOW, LOW_BASIC_CAPABILITIES),
        ],
    )
    def test_returns_basic_capabilities(
        self, test_tmdata_repository, telescope, expected
    ):
        assert test_tmdata_repository.get_basic_capabilities(telescope) == expected

    def test_raises_when_file_missing(self, empty_tmdata_repository):
        with pytest.raises(
            FileNotFoundError, match="file not found: ska1_low/low_capabilities.json"
        ):
            empty_tmdata_repository.get_basic_capabilities(Telescope.LOW)


class TestGetConstraints:
    @pytest.mark.parametrize(
        "telescope, expected",
        [(Telescope.MID, MID_CONSTRAINTS), (Telescope.LOW, LOW_CONSTRAINTS)],
    )
    def test_returns_constraints(self, test_tmdata_repository, telescope, expected):
        assert test_tmdata_repository.get_constraints(telescope) == expected

    def test_raises_when_files_missing(self, empty_tmdata_repository):
        with pytest.raises(
            FileNotFoundError, match="file not found: ska1_mid/mid_capabilities.json"
        ):
            empty_tmdata_repository.get_constraints(Telescope.MID)


class TestGetDefaults:
    @pytest.mark.parametrize(
        "telescope, expected",
        [(Telescope.MID, MID_DEFAULTS), (Telescope.LOW, LOW_DEFAULTS)],
    )
    def test_returns_defaults(self, test_tmdata_repository, telescope, expected):
        assert test_tmdata_repository.get_defaults(telescope) == expected

    def test_raises_when_file_missing(self, empty_tmdata_repository):
        with pytest.raises(
            FileNotFoundError, match="file not found: ska1_mid/mid_defaults.json"
        ):
            empty_tmdata_repository.get_defaults(Telescope.MID)


class TestGetCapabilitySets:
    @pytest.mark.parametrize(
        "telescope, expected",
        [
            (Telescope.MID, [MID_AA1, MID_AA2]),
            (Telescope.LOW, [LOW_AA1, LOW_AA2]),
        ],
    )
    def test_returns_capability_sets_in_file_order(
        self, test_tmdata_repository, telescope, expected
    ):
        assert test_tmdata_repository.get_capability_sets(telescope) == expected

    def test_raises_when_file_missing(self, empty_tmdata_repository):
        with pytest.raises(
            FileNotFoundError, match="file not found: ska1_mid/mid_capabilities.json"
        ):
            empty_tmdata_repository.get_capability_sets(Telescope.MID)


class TestGetCapabilitySet:
    @pytest.mark.parametrize(
        "telescope, name, expected",
        [
            (Telescope.MID, "AA1", MID_AA1),
            (Telescope.MID, "AA2", MID_AA2),
            (Telescope.LOW, "AA1", LOW_AA1),
            (Telescope.LOW, "AA2", LOW_AA2),
        ],
    )
    def test_returns_capability_set(
        self, test_tmdata_repository, telescope, name, expected
    ):
        assert test_tmdata_repository.get_capability_set(telescope, name) == expected

    def test_raises_for_unknown_name(self, test_tmdata_repository):
        with pytest.raises(
            CapabilitySetNotFoundError,
            match=(
                r"Capability set AA3 is invalid for telescope mid\. "
                r"Valid capability sets are AA1, AA2\."
            ),
        ) as excinfo:
            test_tmdata_repository.get_capability_set(Telescope.MID, "AA3")

        assert excinfo.value.telescope == Telescope.MID
        assert excinfo.value.name == "AA3"
        assert excinfo.value.available_names == ["AA1", "AA2"]

    def test_raises_when_file_missing(self, empty_tmdata_repository):
        with pytest.raises(
            FileNotFoundError, match="file not found: ska1_low/low_capabilities.json"
        ):
            empty_tmdata_repository.get_capability_set(Telescope.LOW, "AA1")


class TestGetSubarrayTemplates:
    @pytest.mark.parametrize(
        "telescope, capability_set, expected",
        [
            (Telescope.MID, "AA1", []),
            (Telescope.MID, "AA2", [MID_FULL_AA2_TEMPLATE]),
            (Telescope.LOW, "AA1", [LOW_TEST_AA1_TEMPLATE]),
            (Telescope.LOW, "AA2", [LOW_FULL_AA2_TEMPLATE, LOW_TEST_AA2_TEMPLATE]),
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
            test_tmdata_repository.get_subarray_templates(Telescope.MID, "AA3")


class TestGetCycleCapabilitySets:
    @pytest.mark.parametrize(
        "cycle_id, expected",
        [
            (CycleID(1), {Telescope.LOW: LOW_AA1}),
            (CycleID(2), {Telescope.MID: MID_AA2, Telescope.LOW: LOW_AA2}),
        ],
        ids=["low only", "mid and low"],
    )
    def test_returns_capability_sets_offered(
        self, test_tmdata_repository, cycle_id, expected
    ):
        assert test_tmdata_repository.get_cycle_capability_sets(cycle_id) == expected

    def test_raises_for_unknown_cycle(self, test_tmdata_repository):
        with pytest.raises(CycleNotFoundError):
            test_tmdata_repository.get_cycle_capability_sets(CycleID(3))

    def test_raises_when_cycle_names_unknown_capability_set(
        self, test_tmdata_repository, monkeypatch
    ):
        """The cycle refers to a capability set by name; a name with no
        capability set is an error rather than being skipped."""
        cycle = CYCLE_1.model_copy(
            update={
                "telescope_capabilities": CYCLE_1.telescope_capabilities.model_copy(
                    update={"ska_low": "AA3"}
                )
            }
        )
        # ToDo: this patches the query function the repository wraps, so it
        # depends on the implementation; replace it with a repository over
        # test data that has the broken cycle (see the plan)
        monkeypatch.setattr(queries, "get_cycle", lambda *_: cycle)

        with pytest.raises(CapabilitySetNotFoundError, match="Capability set AA3"):
            test_tmdata_repository.get_cycle_capability_sets(CycleID(1))
