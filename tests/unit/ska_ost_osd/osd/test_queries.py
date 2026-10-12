"""Unit tests for the query functions, using the test copy of the
tmdata in tests/tmdata."""

from datetime import datetime, timezone

import pytest

from ska_ost_osd.osd.exceptions import CycleNotFoundError, OSDQueryError
from ska_ost_osd.osd.models.observatory_policies import (
    CycleID,
    CycleInformation,
    CyclePolicies,
    ObservatoryPolicy,
    TelescopeCapabilities,
)
from ska_ost_osd.osd.queries import get_cycle, get_cycle_ids, get_cycles

# tests/tmdata/cycles/cycle_1.json
CYCLE_1 = ObservatoryPolicy(
    cycle_number=CycleID(1),
    cycle_id="TEST_SKAO_2027_Low_AA2_SV",
    type="Science Verification",
    cycle_description="TEST Low AA2 Science Verification",
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
    telescope_capabilities=TelescopeCapabilities(ska_mid=None, ska_low="AA2_SV"),
)

# tests/tmdata/cycles/cycle_2.json
CYCLE_2 = ObservatoryPolicy(
    cycle_number=CycleID(2),
    cycle_id="TEST_SKAO_2027_Low_AA2_Proposal",
    type="Proposal",
    cycle_description="TEST Low AA2 Proposal",
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


class TestGetCycleIds:
    def test_returns_sorted_cycle_ids(self, tests_tmdata):
        assert get_cycle_ids(tests_tmdata) == [CycleID(1), CycleID(2)]

    def test_raises_when_cycles_directory_missing(self, empty_tmdata):
        with pytest.raises(FileNotFoundError, match="file not found: cycles"):
            get_cycle_ids(empty_tmdata)


class TestGetCycle:
    @pytest.mark.parametrize(
        "cycle_id, expected", [(CycleID(1), CYCLE_1), (CycleID(2), CYCLE_2)]
    )
    def test_returns_cycle(self, tests_tmdata, cycle_id, expected):
        assert get_cycle(tests_tmdata, cycle_id) == expected

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
        assert get_cycles(tests_tmdata) == [CYCLE_1, CYCLE_2]

    def test_raises_when_cycles_directory_missing(self, empty_tmdata):
        with pytest.raises(FileNotFoundError, match="file not found: cycles"):
            get_cycles(empty_tmdata)


class TestExceptions:
    def test_cycle_not_found_is_a_query_error_and_lookup_error(self):
        error = CycleNotFoundError(CycleID(3), [CycleID(1), CycleID(2)])

        assert isinstance(error, OSDQueryError)
        assert isinstance(error, LookupError)
