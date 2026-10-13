"""Unit tests for the views, using the test copy of the tmdata in
tests/tmdata."""

import pytest

from ska_ost_osd.osd.exceptions import CycleNotFoundError
from ska_ost_osd.osd.models.configuration import Configuration, CycleConfiguration
from ska_ost_osd.osd.models.cycles import CycleID
from ska_ost_osd.osd.views import (
    get_configuration,
    get_cycle_configuration,
    get_cycle_configurations,
)
from tests.unit.ska_ost_osd.osd.expected import (
    CONFIGURATION,
    CYCLE_1_CONFIGURATION,
    CYCLE_2_CONFIGURATION,
)

CAPABILITY_SET_KEYS = [
    "name",
    "receptors",
    "available_bandwidth_hz",
    "number_pst_beams",
    "number_fsps",
]


class TestGetConfiguration:
    def test_returns_configuration(self, test_tmdata_repository):
        assert get_configuration(test_tmdata_repository) == CONFIGURATION

    def test_serves_the_odt_configuration_fields(self, test_tmdata_repository):
        """The JSON matches what ska-oso-services serves from GET
        /configuration, with allowed_channel_width_values_hz on the Mid
        capability sets, which ska-oso-services means to serve but drops."""
        served = get_configuration(test_tmdata_repository).model_dump(mode="json")

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

    def test_serialised_configuration_validates(self, test_tmdata_repository):
        configuration = get_configuration(test_tmdata_repository)
        assert Configuration.model_validate(configuration.model_dump()) == configuration

    def test_raises_when_files_missing(self, empty_tmdata_repository):
        with pytest.raises(FileNotFoundError):
            get_configuration(empty_tmdata_repository)


class TestGetCycleConfiguration:
    @pytest.mark.parametrize(
        "cycle_id, expected",
        [(CycleID(1), CYCLE_1_CONFIGURATION), (CycleID(2), CYCLE_2_CONFIGURATION)],
        ids=["low only", "mid and low"],
    )
    def test_returns_cycle_configuration(self, tests_tmdata, cycle_id, expected):
        assert get_cycle_configuration(tests_tmdata, cycle_id) == expected

    def test_raises_for_unknown_cycle(self, tests_tmdata):
        with pytest.raises(CycleNotFoundError):
            get_cycle_configuration(tests_tmdata, CycleID(3))

    def test_serves_the_pht_cycle_fields(self, tests_tmdata):
        """The JSON, with aliases as ska-oso-services serves it, has the
        names the PHT UI reads: telescope_capabilities Mid/Low, Mid's
        basic_capabilities.receiver_information, and under each telescope
        only basic_capabilities and the offered capability set, keyed by
        its name."""
        served = get_cycle_configuration(tests_tmdata, CycleID(2)).model_dump(
            mode="json", by_alias=True
        )

        assert list(served) == ["observatory_policy", "capabilities"]
        assert served["observatory_policy"]["telescope_capabilities"] == {
            "Mid": "AA2",
            "Low": "AA2",
        }
        mid = served["capabilities"]["mid"]
        assert list(mid) == ["basic_capabilities", "AA2"]
        assert list(mid["basic_capabilities"]) == ["receiver_information"]
        assert mid["AA2"]["name"] == "AA2"
        assert list(served["capabilities"]["low"]) == ["basic_capabilities", "AA2"]

    def test_telescope_not_offered_is_null(self, tests_tmdata):
        served = get_cycle_configuration(tests_tmdata, CycleID(1)).model_dump(
            mode="json", by_alias=True
        )
        assert served["capabilities"]["mid"] is None

    @pytest.mark.parametrize("cycle_id", [CycleID(1), CycleID(2)])
    def test_served_cycle_configuration_validates(self, tests_tmdata, cycle_id):
        configuration = get_cycle_configuration(tests_tmdata, cycle_id)
        served = configuration.model_dump(mode="json", by_alias=True)
        assert CycleConfiguration.model_validate(served) == configuration


class TestGetCycleConfigurations:
    def test_returns_every_cycle_in_id_order(self, tests_tmdata):
        assert get_cycle_configurations(tests_tmdata) == [
            CYCLE_1_CONFIGURATION,
            CYCLE_2_CONFIGURATION,
        ]

    def test_raises_when_cycles_directory_missing(self, empty_tmdata):
        with pytest.raises(FileNotFoundError):
            get_cycle_configurations(empty_tmdata)
