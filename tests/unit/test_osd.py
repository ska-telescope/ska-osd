from importlib.metadata import version
from unittest.mock import patch

import pytest

from ska_ost_osd.osd.osd import get_osd_data, osd_tmdata_source, update_file_storage
from ska_ost_osd.osd.osd_update_schema import ValidationOnCapabilities
from tests.conftest import (
    DEFAULT_OSD_RESPONSE_WITH_NO_PARAMETER,
    OSD_RESPONSE_WITH_CAPABILITIES_ARRAY_ASSEMBLY_PARAMETER,
    OSD_RESPONSE_WITH_ONLY_CAPABILITIES_PARAMETER,
    tm_data_osd,
)


@pytest.mark.parametrize(
    "capabilities, array_assembly, tmdata, expected",
    [
        (None, None, tm_data_osd, DEFAULT_OSD_RESPONSE_WITH_NO_PARAMETER),
        (
            ["mid"],
            None,
            tm_data_osd,
            OSD_RESPONSE_WITH_ONLY_CAPABILITIES_PARAMETER,
        ),
        (
            ["mid"],
            "AA0.5",
            tm_data_osd,
            OSD_RESPONSE_WITH_CAPABILITIES_ARRAY_ASSEMBLY_PARAMETER,
        ),
    ],
)
def test_get_osd_data(
    capabilities,
    array_assembly,
    tmdata,  # pylint: disable=W0613
    expected,
    tm_data_osd,  # pylint: disable=W0621
):
    """This test case checks the functionality of get_osd_data
        it converts the python dict into list keys and checks
        for equality with expected output.

    :param capabilities: Mid or Low
    :param array_assembly: Array Assembly AA0.5, AA1
    :param tmdata: tmdata object
    :param expected: output of get_osd_data function
    :param tm_data_osd: tmdata fixture

    :returns: assert equals values
    """

    result, _ = get_osd_data(capabilities, array_assembly, tmdata=tm_data_osd)
    result_keys = list(result["capabilities"].keys())
    expected_keys = list(expected["capabilities"].keys())

    assert result_keys == expected_keys


def test_set_source_car_method(validate_car_class):
    """This test case checks if the output of the osd_tmdata_source
        function is as expected or not.

    :param osd_tmdata_source: validate_car_class fixture.
    """

    assert validate_car_class == ("car:ost/ska-ost-osd?1.11.0#tmdata",)


def test_set_source_gitlab_method(validate_gitlab_class):
    """This test case checks if the output of the osd_tmdata_source
        function is as expected or not.

    :param osd_tmdata_source: validate_gitlab_class fixture.
    """

    msg = "nak-776-osd-implementation-file-versioning#tmdata"

    assert validate_gitlab_class == (
        f"gitlab://gitlab.com/ska-telescope/ost/ska-ost-osd?{msg}",
    )


def test_validate_gitlab_with_both_invalid_param():
    """This test case checks if the output of the osd_tmdata_source
    when no parameter is given and latest version is
    returned or not
    """

    ost_osd_version = version("ska_ost_osd")

    msg = f"car:ost/ska-ost-osd?{ost_osd_version}#tmdata"
    tm_data_src, _ = osd_tmdata_source()

    assert tm_data_src == (msg,)


def test_check_osd_version_method():
    """This test case checks if the output of the osd_tmdata_source
    when osd_version parameter is given it should return the correct URL
    """
    tm_data_src, _ = osd_tmdata_source(osd_version="1.0.0")
    assert tm_data_src == ("car:ost/ska-ost-osd?1.0.0#tmdata",)


def test_check_cycle_id_and_osd_version_method():
    """This test case checks if the output of the osd_tmdata_source
    when cycle_id and osd_version parameter is given
    it should return the correct URL
    """
    tm_data_src, _ = osd_tmdata_source(cycle_id=1, osd_version="1.11.0")
    assert tm_data_src == ("car:ost/ska-ost-osd?1.11.0#tmdata",)


def test_check_cycle_id_2_and_osd_version_method():
    """This test case checks if the output of the osd_tmdata_source
    when cycle_id and osd_version parameter is given
    it should return the correct URL
    """
    tm_data_src, _ = osd_tmdata_source(cycle_id=2, osd_version="1.0.0")
    assert tm_data_src == ("car:ost/ska-ost-osd?1.0.0#tmdata",)


def test_check_cycle_id_with_source_method():
    """This test case checks if the output of the osd_tmdata_source
    when cycle_id, osd_version and source parameter is given
    it should return the correct URL
    """
    tm_data_src, _ = osd_tmdata_source(cycle_id=2, osd_version="1.0.0", source="file")
    assert tm_data_src == ("file://tmdata",)


def test_check_master_branch_method():
    """This test case checks if the output of the osd_tmdata_source
    when cycle_id, gitlab_branch and source parameter is given
    it should return the correct URL
    """
    tm_data_src, _ = osd_tmdata_source(
        cycle_id=2, gitlab_branch="master", source="gitlab"
    )
    assert tm_data_src == (
        "gitlab://gitlab.com/ska-telescope/ost/ska-ost-osd?master#tmdata",
    )


def test_invalid_osd_tmdata_source():
    """This test case checks if the output of the osd_tmdata_source
    when cycle_id, gitlab_branch and source parameter and osd_version is given incorrect
    it should return the appropriate error messages.
    """

    _, error_msgs = osd_tmdata_source(
        cycle_id=100000,
        osd_version="1.1.0",
        gitlab_branch="main",
        source="github",
    )
    assert error_msgs == [
        "Source is not valid available are file, car, gitlab",
        "Only one parameter is needed either osd_version or gitlab_branch",
        "Cycle 100000 is not valid,Available IDs are 1",
    ]


def test_invalid_source(osd_versions):
    """This test case checks when gitlab_branch is given source
    should be gitlab else will raise / return error.
    NOTE: This testcase has dependency on 'cycle_gitlab_release_version_mapping.json'
          file so make sure to run the 'make osd-pre-release' command which is
          mentioned in readme and document files.
    """
    _, error_msgs = osd_tmdata_source(
        cycle_id=1,
        gitlab_branch="main",
        source="file",
    )

    expected_error_msg = ", ".join([str(err) for err in error_msgs])

    assert (
        expected_error_msg
        == "Source file is not valid, OSD Version main is not valid,Available OSD"
        f" Versions are {osd_versions}"
    )


def test_invalid_get_osd_data_capability(tm_data_osd):  # pylint: disable=W0621
    """This test case checks if the output of the get_osd_data
    when capabilities is given incorrect with correct array_assembly
    it should return the appropriate error messages.

    :param tm_data_osd: tm_data_osd
    """

    _, error_msgs = get_osd_data(
        capabilities=["midd"], array_assembly="AA1", tmdata=tm_data_osd
    )
    assert error_msgs == [
        "Capability midd is not valid,Available Capabilities are low, mid,"
        " observatory_policies"
    ]


def test_invalid_get_osd_data_array_assembly(tm_data_osd):  # pylint: disable=W0621
    """This test case checks if the output of the get_osd_data
    when array_assembly is given incorrect with correct capabilities
    it should return the appropriate error messages.

    :param tm_data_osd: tm_data_osd
    """
    aa_value = "AA100000"

    _, error_msgs = get_osd_data(
        capabilities=["mid"], array_assembly=aa_value, tmdata=tm_data_osd
    )
    msg = ",".join(error_msgs[0].split(",")[1:])

    assert error_msgs[0] == f"Array Assembly {aa_value} is not valid,{msg}"


@pytest.fixture
def sample_existing_data():
    return {
        "telescope": "SKA-Mid",
        "basic_capabilities": {
            "max_frequency": 15.3e9,
            "min_frequency": 350e6,
        },
        "AA0.5": {
            "max_baseline": 1000,
            "num_stations": 64,
        },
    }


def test_update_file_storage_1():
    """
    Test update_file_storage function when updating nested dictionary
    fields and observatory policy.
    """
    validated_capabilities = {
        "capabilities": {
            "mid": {
                "AA0.5": {
                    "existing_key": {"nested_key": "new_value"},
                    "new_key": "new_value",
                }
            }
        }
    }
    validated_capabilities = ValidationOnCapabilities(**validated_capabilities)
    observatory_policy = {"new_policy": "value"}
    existing_stored_data = {
        "AA0.5": {
            "existing_key": {
                "nested_key": "old_value",
                "untouched_key": "untouched_value",
            },
            "untouched_field": "untouched_value",
        }
    }

    expected_updated_data = {
        "AA0.5": {
            "existing_key": {"nested_key": "new_value"},
            "untouched_field": "untouched_value",
            "new_key": "new_value",
        }
    }

    with patch("ska_ost_osd.osd.osd.update_file"):
        updated_data = update_file_storage(
            validated_capabilities, observatory_policy, existing_stored_data
        )
    assert updated_data == expected_updated_data


def test_update_file_storage_invalid_input(
    sample_existing_data,
):  # pylint: disable=W0621
    """Test update_file_storage with invalid input structure"""
    invalid_input = {"invalid_key": {"telescope": "SKA-Mid"}}
    with patch("ska_ost_osd.osd.osd.update_file"):
        with pytest.raises(AttributeError):
            update_file_storage(invalid_input, {}, sample_existing_data)


def test_update_file_storage_nested_dict_update(
    sample_existing_data, mocker
):  # pylint: disable=W0621
    """Test update_file_storage with nested dictionary updates"""
    mock_update_file = mocker.patch("ska_ost_osd.osd.osd.update_file")

    update_data = {
        "capabilities": {
            "SKA-Mid": {
                "basic_capabilities": {
                    "new_capability": "value",
                    "max_frequency": 16e9,  # Updating existing value
                },
                "AA0.5": {
                    "new_field": "new_value",
                },
            }
        }
    }
    validated_capabilities = ValidationOnCapabilities(**update_data)
    result = update_file_storage(validated_capabilities, {}, sample_existing_data)

    assert result["basic_capabilities"]["new_capability"] == "value"
    assert result["basic_capabilities"]["max_frequency"] == 16e9
    assert result["AA0.5"]["new_field"] == "new_value"
    assert result["AA0.5"]["max_baseline"] == 1000  # Existing value should be preserved

    mock_update_file.assert_called_once()


def test_update_file_storage_non_existent_telescope(
    sample_existing_data, mocker
):  # pylint: disable=W0621
    mock_update_file = mocker.patch("ska_ost_osd.osd.osd.update_file")
    non_existent_telescope = {
        "capabilities": {
            "SKA-Low": {  # This telescope doesn't exist in the sample data
                "basic_capabilities": {
                    "max_frequency": 350e6,
                }
            }
        }
    }
    validated_capabilities = ValidationOnCapabilities(**non_existent_telescope)
    result = update_file_storage(validated_capabilities, {}, sample_existing_data)
    assert "SKA-Low" not in result
    mock_update_file.assert_called_once()


def test_update_file_storage_observatory_policy_update(
    sample_existing_data, mocker
):  # pylint: disable=W0621
    """Test update_file_storage with observatory policy updates"""
    mock_update_file = mocker.patch("ska_ost_osd.osd.osd.update_file")

    update_data = {
        "capabilities": {
            "SKA-Mid": {
                "basic_capabilities": {
                    "new_capability": "value",
                }
            }
        }
    }

    observatory_policy = {"new_policy": "value"}
    validated_capabilities = ValidationOnCapabilities(**update_data)
    update_file_storage(
        validated_capabilities, observatory_policy, sample_existing_data
    )

    assert mock_update_file.call_count == 2
