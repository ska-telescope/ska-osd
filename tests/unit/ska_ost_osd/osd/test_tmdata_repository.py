"""Unit tests for the TMData repository, using the test copy of the tmdata in
tests/tmdata."""

import pytest

from ska_ost_osd.osd.common.constant import Telescope
from ska_ost_osd.osd.exceptions import CycleNotFoundError
from ska_ost_osd.osd.models.cycles import Cycle, CycleID
from tests.unit.ska_ost_osd.osd.expected import (
    CYCLE_1,
    CYCLE_2,
    LOW_BASIC_CAPABILITIES,
    MID_BASIC_CAPABILITIES,
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
