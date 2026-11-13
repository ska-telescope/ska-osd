"""Unit tests for the TMData storage readers, which read each tmdata file into
its storage model, using the test copy of the tmdata in tests/tmdata."""

import pytest

from ska_ost_osd.osd.adapters.tmdata.storage import (
    get_capability_set_files,
    get_cycle_file,
    get_subarray_template_library,
    get_telescope_basic_capabilities,
    get_telescope_defaults,
)
from ska_ost_osd.osd.common.constant import Telescope
from tests.unit.ska_ost_osd.osd.expected import (
    CYCLE_1_FILE,
    CYCLE_2_FILE,
    LOW_AA1_SUBARRAY_TEMPLATE_LIBRARY_FILE,
    LOW_AA2_SUBARRAY_TEMPLATE_LIBRARY_FILE,
    LOW_BASIC_CAPABILITIES,
    LOW_CAPABILITY_SET_FILES,
    LOW_DEFAULTS_FILE,
    MID_AA2_SUBARRAY_TEMPLATE_LIBRARY_FILE,
    MID_BASIC_CAPABILITIES,
    MID_CAPABILITY_SET_FILES,
    MID_DEFAULTS_FILE,
)


class TestGetCycleFile:
    @pytest.mark.parametrize(
        "cycle_id, expected",
        [
            ("TEST_SKAO_2027_Low_AA1_SV", CYCLE_1_FILE),
            ("TEST_SKAO_2027_AA2_Proposal", CYCLE_2_FILE),
        ],
    )
    def test_returns_cycle_file(self, tests_tmdata, cycle_id, expected):
        assert get_cycle_file(tests_tmdata, cycle_id) == expected

    def test_raises_when_file_missing(self, empty_tmdata):
        with pytest.raises(FileNotFoundError, match="file not found: cycles"):
            get_cycle_file(empty_tmdata, "TEST_SKAO_2027_Low_AA1_SV")

    def test_raises_when_no_file_has_cycle_id(self, tests_tmdata):
        with pytest.raises(
            FileNotFoundError,
            match="file not found: no cycle file in cycles has id NO_SUCH_CYCLE",
        ):
            get_cycle_file(tests_tmdata, "NO_SUCH_CYCLE")


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
            (Telescope.SKA_MID, "telescopes/ska_mid/array_assemblies"),
            (Telescope.SKA_LOW, "telescopes/ska_low/array_assemblies"),
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
            (Telescope.SKA_MID, "telescopes/ska_mid/basic_capabilities.json"),
            (Telescope.SKA_LOW, "telescopes/ska_low/basic_capabilities.json"),
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
            (Telescope.SKA_MID, "telescopes/ska_mid/defaults.json"),
            (Telescope.SKA_LOW, "telescopes/ska_low/defaults.json"),
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
            (Telescope.SKA_MID, "telescopes/ska_mid/subarray_templates/AA2.json"),
            (Telescope.SKA_LOW, "telescopes/ska_low/subarray_templates/AA2.json"),
        ],
    )
    def test_raises_when_file_missing(self, empty_tmdata, telescope, path):
        with pytest.raises(FileNotFoundError, match=f"file not found: {path}"):
            get_subarray_template_library(empty_tmdata, telescope, "AA2")
