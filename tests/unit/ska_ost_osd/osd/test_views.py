"""Unit tests for the views, using the test copy of the tmdata in
tests/tmdata."""

import pytest

from ska_ost_osd.osd.models.configuration import Configuration
from ska_ost_osd.osd.views import get_configuration
from tests.unit.ska_ost_osd.osd.expected import CONFIGURATION

CAPABILITY_SET_KEYS = [
    "name",
    "receptors",
    "available_bandwidth_hz",
    "number_pst_beams",
    "number_fsps",
]


class TestGetConfiguration:
    def test_returns_configuration(self, tests_tmdata):
        assert get_configuration(tests_tmdata) == CONFIGURATION

    def test_serves_the_odt_configuration_fields(self, tests_tmdata):
        """The JSON matches what ska-oso-services serves from GET
        /configuration, with allowed_channel_width_values_hz on the Mid
        capability sets, which ska-oso-services means to serve but drops."""
        served = get_configuration(tests_tmdata).model_dump(mode="json")

        assert list(served) == ["ska_mid", "ska_low"]
        assert list(served["ska_mid"]) == [
            "frequency_band",
            "constraints",
            "subarrays",
            "spfrx_defaults",
        ]
        assert list(served["ska_low"]) == [
            "frequency_band",
            "constraints",
            "quality_attribute_metrics",
            "subarrays",
        ]
        assert list(served["ska_mid"]["subarrays"][0]) == [
            *CAPABILITY_SET_KEYS,
            "allowed_channel_width_values_hz",
        ]
        assert list(served["ska_low"]["subarrays"][0]) == [
            *CAPABILITY_SET_KEYS,
            "number_substations",
            "number_subarray_beams",
        ]
        assert served["ska_low"]["quality_attribute_metrics"] == {
            "cbf": {"processors_ready_percent": 100.0}
        }

    def test_serialised_configuration_validates(self, tests_tmdata):
        configuration = get_configuration(tests_tmdata)
        assert Configuration.model_validate(configuration.model_dump()) == configuration

    def test_raises_when_files_missing(self, empty_tmdata):
        with pytest.raises(FileNotFoundError):
            get_configuration(empty_tmdata)
