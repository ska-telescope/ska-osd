"""Unit tests for the TMData storage readers, which read each tmdata file into
its storage model, using the test copy of the tmdata in tests/tmdata."""

import pytest

from ska_ost_osd.osd.adapters.tmdata.storage import (
    get_capability_set_files,
    get_cycle_file,
    get_subarray_template_library,
    get_telescope_basic_capabilities,
    get_telescope_capabilities,
    get_telescope_defaults,
)
from ska_ost_osd.osd.common.constant import Telescope
from ska_ost_osd.osd.models.cycles import CycleID
from tests.unit.ska_ost_osd.osd.expected import (
    CYCLE_1_FILE,
    CYCLE_2_FILE,
    LOW_AA1_SUBARRAY_TEMPLATE_LIBRARY_FILE,
    LOW_AA2_SUBARRAY_TEMPLATE_LIBRARY_FILE,
    LOW_BASIC_CAPABILITIES,
    LOW_CAPABILITIES_FILE,
    LOW_CAPABILITY_SET_FILES,
    LOW_DEFAULTS_FILE,
    MID_AA2_SUBARRAY_TEMPLATE_LIBRARY_FILE,
    MID_BASIC_CAPABILITIES,
    MID_CAPABILITIES_FILE,
    MID_CAPABILITY_SET_FILES,
    MID_DEFAULTS_FILE,
)


class TestGetCycleFile:
    @pytest.mark.parametrize(
        "cycle_id, expected",
        [(CycleID(1), CYCLE_1_FILE), (CycleID(2), CYCLE_2_FILE)],
    )
    def test_returns_cycle_file(self, tests_tmdata, cycle_id, expected):
        assert get_cycle_file(tests_tmdata, cycle_id) == expected

    def test_raises_when_file_missing(self, empty_tmdata):
        with pytest.raises(
            FileNotFoundError, match="file not found: cycles/cycle_1.json"
        ):
            get_cycle_file(empty_tmdata, CycleID(1))


class TestGetTelescopeCapabilities:
    @pytest.mark.parametrize(
        "telescope, expected",
        [
            (Telescope.SKA_MID, MID_CAPABILITIES_FILE),
            (Telescope.SKA_LOW, LOW_CAPABILITIES_FILE),
        ],
    )
    def test_returns_capabilities(self, tests_tmdata, telescope, expected):
        assert get_telescope_capabilities(tests_tmdata, telescope) == expected

    @pytest.mark.parametrize(
        "telescope, path",
        [
            (Telescope.SKA_MID, "ska1_mid/mid_capabilities.json"),
            (Telescope.SKA_LOW, "ska1_low/low_capabilities.json"),
        ],
    )
    def test_raises_when_file_missing(self, empty_tmdata, telescope, path):
        with pytest.raises(FileNotFoundError, match=f"file not found: {path}"):
            get_telescope_capabilities(empty_tmdata, telescope)


class TestGetCapabilitySetFiles:
    @pytest.mark.parametrize(
        "telescope, expected",
        [
            (Telescope.SKA_MID, MID_CAPABILITY_SET_FILES),
            (Telescope.SKA_LOW, LOW_CAPABILITY_SET_FILES),
        ],
    )
    def test_returns_capability_sets_named_by_file(
        self, tests_tmdata, telescope, expected
    ):
        assert get_capability_set_files(tests_tmdata, telescope) == expected

    @pytest.mark.parametrize(
        "telescope, path",
        [
            (Telescope.SKA_MID, "ska1_mid/capabilities"),
            (Telescope.SKA_LOW, "ska1_low/capabilities"),
        ],
    )
    def test_raises_when_directory_missing(self, empty_tmdata, telescope, path):
        with pytest.raises(FileNotFoundError, match=f"file not found: {path}"):
            get_capability_set_files(empty_tmdata, telescope)


class TestGetTelescopeBasicCapabilities:
    @pytest.mark.parametrize(
        "telescope, expected",
        [
            (Telescope.SKA_MID, MID_BASIC_CAPABILITIES),
            (Telescope.SKA_LOW, LOW_BASIC_CAPABILITIES),
        ],
    )
    def test_returns_basic_capabilities(self, tests_tmdata, telescope, expected):
        assert get_telescope_basic_capabilities(tests_tmdata, telescope) == expected

    @pytest.mark.parametrize(
        "telescope, path",
        [
            (Telescope.SKA_MID, "ska1_mid/basic_capabilities.json"),
            (Telescope.SKA_LOW, "ska1_low/basic_capabilities.json"),
        ],
    )
    def test_raises_when_file_missing(self, empty_tmdata, telescope, path):
        with pytest.raises(FileNotFoundError, match=f"file not found: {path}"):
            get_telescope_basic_capabilities(empty_tmdata, telescope)


class TestGetTelescopeDefaults:
    @pytest.mark.parametrize(
        "telescope, expected",
        [
            (Telescope.SKA_MID, MID_DEFAULTS_FILE),
            (Telescope.SKA_LOW, LOW_DEFAULTS_FILE),
        ],
    )
    def test_returns_defaults(self, tests_tmdata, telescope, expected):
        assert get_telescope_defaults(tests_tmdata, telescope) == expected

    @pytest.mark.parametrize(
        "telescope, path",
        [
            (Telescope.SKA_MID, "ska1_mid/mid_defaults.json"),
            (Telescope.SKA_LOW, "ska1_low/low_defaults.json"),
        ],
    )
    def test_raises_when_file_missing(self, empty_tmdata, telescope, path):
        with pytest.raises(FileNotFoundError, match=f"file not found: {path}"):
            get_telescope_defaults(empty_tmdata, telescope)


class TestGetSubarrayTemplateLibrary:
    @pytest.mark.parametrize(
        "telescope, array_assembly, expected",
        [
            (Telescope.SKA_MID, "AA2", MID_AA2_SUBARRAY_TEMPLATE_LIBRARY_FILE),
            (Telescope.SKA_LOW, "AA1", LOW_AA1_SUBARRAY_TEMPLATE_LIBRARY_FILE),
            (Telescope.SKA_LOW, "AA2", LOW_AA2_SUBARRAY_TEMPLATE_LIBRARY_FILE),
        ],
    )
    def test_returns_library_file(
        self, tests_tmdata, telescope, array_assembly, expected
    ):
        assert (
            get_subarray_template_library(tests_tmdata, telescope, array_assembly)
            == expected
        )

    @pytest.mark.parametrize(
        "telescope, path",
        [
            (Telescope.SKA_MID, "ska1_mid/subarray_templates/AA2.json"),
            (Telescope.SKA_LOW, "ska1_low/subarray_templates/AA2.json"),
        ],
    )
    def test_raises_when_file_missing(self, empty_tmdata, telescope, path):
        with pytest.raises(FileNotFoundError, match=f"file not found: {path}"):
            get_subarray_template_library(empty_tmdata, telescope, "AA2")
