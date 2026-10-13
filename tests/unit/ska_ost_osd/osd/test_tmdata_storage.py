"""Unit tests for the TMData storage readers, which read each tmdata file into
its storage model, using the test copy of the tmdata in tests/tmdata."""

import pytest

from ska_ost_osd.osd.common.constant import Telescope
from ska_ost_osd.osd.queries import (
    get_subarray_template_library,
    get_telescope_capabilities,
    get_telescope_defaults,
)
from tests.unit.ska_ost_osd.osd.expected import (
    LOW_CAPABILITIES_FILE,
    LOW_DEFAULTS_FILE,
    MID_CAPABILITIES_FILE,
    MID_DEFAULTS_FILE,
    SUBARRAY_TEMPLATE_LIBRARY_FILE,
)


class TestGetTelescopeCapabilities:
    @pytest.mark.parametrize(
        "telescope, expected",
        [
            (Telescope.MID, MID_CAPABILITIES_FILE),
            (Telescope.LOW, LOW_CAPABILITIES_FILE),
        ],
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
        [(Telescope.MID, MID_DEFAULTS_FILE), (Telescope.LOW, LOW_DEFAULTS_FILE)],
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


class TestGetSubarrayTemplateLibrary:
    def test_returns_library_file(self, tests_tmdata):
        assert (
            get_subarray_template_library(tests_tmdata)
            == SUBARRAY_TEMPLATE_LIBRARY_FILE
        )

    def test_raises_when_file_missing(self, empty_tmdata):
        with pytest.raises(
            FileNotFoundError,
            match="file not found: subarray_templates/subarray_template_library.json",
        ):
            get_subarray_template_library(empty_tmdata)
