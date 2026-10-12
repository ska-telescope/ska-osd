"""Unit tests for the query functions, using the test copy of the
tmdata in tests/tmdata."""

import pytest

from ska_ost_osd.osd.common.constant import Telescope
from ska_ost_osd.osd.exceptions import (
    CapabilitySetNotFoundError,
    CycleNotFoundError,
    OSDQueryError,
)
from ska_ost_osd.osd.models.observatory_policies import CycleID
from ska_ost_osd.osd.queries import (
    get_capability_set,
    get_capability_sets,
    get_cycle,
    get_cycle_ids,
    get_cycles,
    get_telescope_capabilities,
    get_telescope_defaults,
)
from tests.unit.ska_ost_osd.osd.expected import (
    CYCLE_1,
    CYCLE_2,
    LOW_AA05,
    LOW_AA1,
    LOW_CAPABILITIES,
    LOW_DEFAULTS,
    MID_AA05,
    MID_AA1,
    MID_CAPABILITIES,
    MID_DEFAULTS,
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


class TestGetTelescopeCapabilities:
    @pytest.mark.parametrize(
        "telescope, expected",
        [(Telescope.MID, MID_CAPABILITIES), (Telescope.LOW, LOW_CAPABILITIES)],
    )
    def test_returns_capabilities(self, tests_tmdata, telescope, expected):
        assert get_telescope_capabilities(tests_tmdata, telescope) == expected

    @pytest.mark.parametrize(
        "telescope, path",
        [
            (Telescope.MID, "ska1_mid/mid_capabilities.json"),
            (Telescope.LOW, "ska1_low/low_capabilities.json"),
        ],
    )
    def test_raises_when_file_missing(self, empty_tmdata, telescope, path):
        with pytest.raises(FileNotFoundError, match=f"file not found: {path}"):
            get_telescope_capabilities(empty_tmdata, telescope)


class TestGetTelescopeDefaults:
    @pytest.mark.parametrize(
        "telescope, expected",
        [(Telescope.MID, MID_DEFAULTS), (Telescope.LOW, LOW_DEFAULTS)],
    )
    def test_returns_defaults(self, tests_tmdata, telescope, expected):
        assert get_telescope_defaults(tests_tmdata, telescope) == expected

    @pytest.mark.parametrize(
        "telescope, path",
        [
            (Telescope.MID, "ska1_mid/mid_defaults.json"),
            (Telescope.LOW, "ska1_low/low_defaults.json"),
        ],
    )
    def test_raises_when_file_missing(self, empty_tmdata, telescope, path):
        with pytest.raises(FileNotFoundError, match=f"file not found: {path}"):
            get_telescope_defaults(empty_tmdata, telescope)


class TestGetCapabilitySets:
    @pytest.mark.parametrize(
        "telescope, expected",
        [
            (Telescope.MID, [MID_AA05, MID_AA1]),
            (Telescope.LOW, [LOW_AA05, LOW_AA1]),
        ],
    )
    def test_returns_capability_sets_in_file_order(
        self, tests_tmdata, telescope, expected
    ):
        assert get_capability_sets(tests_tmdata, telescope) == expected

    def test_raises_when_file_missing(self, empty_tmdata):
        with pytest.raises(
            FileNotFoundError, match="file not found: ska1_mid/mid_capabilities.json"
        ):
            get_capability_sets(empty_tmdata, Telescope.MID)


class TestGetCapabilitySet:
    @pytest.mark.parametrize(
        "telescope, name, expected",
        [
            (Telescope.MID, "AA0.5", MID_AA05),
            (Telescope.MID, "AA1", MID_AA1),
            (Telescope.LOW, "AA0.5", LOW_AA05),
            (Telescope.LOW, "AA1", LOW_AA1),
        ],
    )
    def test_returns_capability_set(self, tests_tmdata, telescope, name, expected):
        assert get_capability_set(tests_tmdata, telescope, name) == expected

    def test_raises_for_unknown_name(self, tests_tmdata):
        with pytest.raises(
            CapabilitySetNotFoundError,
            match=(
                r"Capability set AA2 is invalid for telescope mid\. "
                r"Valid capability sets are AA0\.5, AA1\."
            ),
        ) as excinfo:
            get_capability_set(tests_tmdata, Telescope.MID, "AA2")

        assert excinfo.value.telescope == Telescope.MID
        assert excinfo.value.name == "AA2"
        assert excinfo.value.available_names == ["AA0.5", "AA1"]

    def test_raises_when_file_missing(self, empty_tmdata):
        with pytest.raises(
            FileNotFoundError, match="file not found: ska1_low/low_capabilities.json"
        ):
            get_capability_set(empty_tmdata, Telescope.LOW, "AA0.5")


class TestExceptions:
    def test_cycle_not_found_is_a_query_error_and_lookup_error(self):
        error = CycleNotFoundError(CycleID(3), [CycleID(1), CycleID(2)])

        assert isinstance(error, OSDQueryError)
        assert isinstance(error, LookupError)

    def test_capability_set_not_found_is_a_query_error_and_lookup_error(self):
        error = CapabilitySetNotFoundError(Telescope.LOW, "AA2", ["AA0.5", "AA1"])

        assert isinstance(error, OSDQueryError)
        assert isinstance(error, LookupError)
