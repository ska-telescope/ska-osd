"""Unit tests for the query functions, using the test copy of the
tmdata in tests/tmdata."""

import pytest

from ska_ost_osd.osd.exceptions import CycleNotFoundError, OSDQueryError
from ska_ost_osd.osd.models.observatory_policies import CycleID, ObservatoryPolicy
from ska_ost_osd.osd.queries import get_cycle, get_cycle_ids, get_cycles


class TestGetCycleIds:
    def test_returns_sorted_cycle_ids(self, tests_tmdata):
        assert get_cycle_ids(tests_tmdata) == [CycleID(1), CycleID(2)]

    def test_raises_when_cycles_directory_missing(self, empty_tmdata):
        with pytest.raises(FileNotFoundError, match="file not found: cycles"):
            get_cycle_ids(empty_tmdata)


class TestGetCycle:
    @pytest.mark.parametrize(
        "cycle_id, cycle_type, mid, low",
        [
            (CycleID(1), "Science Verification", None, "AA2_SV"),
            (CycleID(2), "Proposal", "AA2", "AA2"),
        ],
    )
    def test_returns_cycle(self, tests_tmdata, cycle_id, cycle_type, mid, low):
        cycle = get_cycle(tests_tmdata, cycle_id)

        assert isinstance(cycle, ObservatoryPolicy)
        assert cycle.cycle_number == cycle_id
        assert cycle.type == cycle_type
        assert cycle.telescope_capabilities.ska_mid == mid
        assert cycle.telescope_capabilities.ska_low == low

    def test_raises_for_unknown_cycle(self, tests_tmdata):
        with pytest.raises(
            CycleNotFoundError, match=r"Cycle 3 is invalid\. Valid IDs are 1,2\."
        ) as excinfo:
            get_cycle(tests_tmdata, CycleID(3))

        assert excinfo.value.cycle_id == 3
        assert excinfo.value.available_cycle_ids == [1, 2]

    def test_raises_when_cycles_directory_missing(self, empty_tmdata):
        with pytest.raises(FileNotFoundError, match="file not found: cycles"):
            get_cycle(empty_tmdata, CycleID(1))


class TestGetCycles:
    def test_returns_every_cycle_in_id_order(self, tests_tmdata):
        cycles = get_cycles(tests_tmdata)

        assert all(isinstance(cycle, ObservatoryPolicy) for cycle in cycles)
        assert [cycle.cycle_number for cycle in cycles] == [CycleID(1), CycleID(2)]

    def test_matches_get_cycle(self, tests_tmdata):
        assert get_cycles(tests_tmdata) == [
            get_cycle(tests_tmdata, cycle_id)
            for cycle_id in get_cycle_ids(tests_tmdata)
        ]

    def test_raises_when_cycles_directory_missing(self, empty_tmdata):
        with pytest.raises(FileNotFoundError, match="file not found: cycles"):
            get_cycles(empty_tmdata)


class TestExceptions:
    def test_cycle_not_found_is_a_query_error_and_lookup_error(self):
        error = CycleNotFoundError(CycleID(3), [CycleID(1), CycleID(2)])

        assert isinstance(error, OSDQueryError)
        assert isinstance(error, LookupError)
