"""Unit tests for the query functions, using the test copy of the
tmdata in tests/tmdata."""

import pytest

from ska_ost_osd.osd.models.observatory_policies import CycleID
from ska_ost_osd.osd.queries import get_cycle_ids


class TestGetCycleIds:
    def test_returns_sorted_cycle_ids(self, tests_tmdata):
        assert get_cycle_ids(tests_tmdata) == [CycleID(1), CycleID(2)]

    def test_raises_when_cycles_directory_missing(self, empty_tmdata):
        with pytest.raises(FileNotFoundError, match="file not found: cycles"):
            get_cycle_ids(empty_tmdata)
