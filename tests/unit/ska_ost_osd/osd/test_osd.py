from unittest.mock import patch

import pytest

from ska_ost_osd.osd.common.error_handling import OSDModelError
from ska_ost_osd.osd.models.models import OSDModel, ValidationOnCapabilities
from ska_ost_osd.osd.osd import get_osd_data, update_osd_file


@pytest.mark.parametrize(
    "capabilities, array_assembly, expected_keys",
    [
        (None, None, ["mid", "low"]),
        (
            ["mid"],
            None,
            ["mid"],
        ),
        (
            ["mid"],
            "AA0.5",
            ["mid"],
        ),
    ],
)
def test_get_osd_data(
    capabilities,
    array_assembly,
    expected_keys,
    tests_tmdata,
):
    """This test case checks the functionality of get_osd_data it converts the
    python dict into list keys and checks for equality with expected output.

    :param capabilities: Mid or Low
    :param array_assembly: Array Assembly AA0.5, AA1
    :param expected: output of get_osd_data function
    :param tests_tmdata: tmdata fixture
    :returns: assert equals values
    """

    result, _ = get_osd_data(
        capabilities, array_assembly, tmdata=tests_tmdata, process_templates=False
    )
    result_keys = list(result["capabilities"].keys())

    assert result_keys == expected_keys


def test_invalid_get_osd_data_capability(tests_tmdata):
    """This test case checks if the output of the get_osd_data when
    capabilities is given incorrect with correct array_assembly it should
    return the appropriate error messages.

    :param tests_tmdata: tests_tmdata
    """

    _, error_msgs = get_osd_data(
        capabilities=["midd"],
        array_assembly="AA1",
        tmdata=tests_tmdata,
        process_templates=False,
    )
    assert error_msgs == [
        "Capability midd is not valid,Available Capabilities are low, mid,"
        " observatory_policies"
    ]


def test_invalid_get_osd_data_array_assembly(tests_tmdata):
    """This test case checks if the output of the get_osd_data when
    array_assembly is given incorrect with correct capabilities it should
    return the appropriate error messages.

    :param tests_tmdata: tests_tmdata
    """
    aa_value = "AA100000"

    _, error_msgs = get_osd_data(
        capabilities=["mid"],
        array_assembly=aa_value,
        tmdata=tests_tmdata,
        process_templates=False,
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


def test_update_osd_file_1():
    """Test update_osd_file function when updating nested dictionary fields
    and observatory policy."""
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
        updated_data = update_osd_file(
            validated_capabilities,
            observatory_policy,
            existing_stored_data,
            telescope="mid",
        )
    assert updated_data == expected_updated_data


def test_update_osd_file_invalid_input(
    sample_existing_data,
):  # pylint: disable=W0621
    """Test update_osd_file with invalid input structure."""
    invalid_input = {"invalid_key": {"telescope": "SKA-Mid"}}
    with patch("ska_ost_osd.osd.osd.update_file"):
        with pytest.raises(AttributeError):
            update_osd_file(invalid_input, {}, sample_existing_data, telescope="mid")


def test_update_osd_file_nested_dict_update(
    sample_existing_data,
):  # pylint: disable=W0621
    """Test update_osd_file with nested dictionary updates."""

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
    result = update_osd_file(
        validated_capabilities, {}, sample_existing_data, telescope="mid"
    )

    assert result["basic_capabilities"]["new_capability"] == "value"
    assert result["basic_capabilities"]["max_frequency"] == 16e9
    assert result["AA0.5"]["new_field"] == "new_value"
    assert result["AA0.5"]["max_baseline"] == 1000  # Existing value should be preserved


def test_update_osd_file_non_existent_telescope(
    sample_existing_data,
):  # pylint: disable=W0621
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
    result = update_osd_file(
        validated_capabilities, {}, sample_existing_data, telescope="low"
    )
    assert "SKA-Low" not in result


def test_update_osd_file_observatory_policy_update(
    sample_existing_data, mocker
):  # pylint: disable=W0621
    """Test update_osd_file with observatory policy updates."""
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
    update_osd_file(
        validated_capabilities,
        observatory_policy,
        sample_existing_data,
        telescope="mid",
    )

    assert mock_update_file.call_count == 1


def test_get_osd_data_with_process_templates(tests_tmdata):
    """Test that process_templates parameter is properly passed through."""
    # Test with process_templates=False (default)
    result_false, _ = get_osd_data(
        capabilities=["mid"],
        array_assembly="AA0.5",
        tmdata=tests_tmdata,
        process_templates=False,
    )

    # Test with process_templates=True
    result_true, _ = get_osd_data(
        capabilities=["mid"],
        array_assembly="AA0.5",
        tmdata=tests_tmdata,
        process_templates=True,
    )

    # Both should return valid data structures
    assert "capabilities" in result_false
    assert "capabilities" in result_true
    assert "mid" in result_false["capabilities"]
    assert "mid" in result_true["capabilities"]


@patch("ska_ost_osd.osd.osd.process_template_mappings")
def test_get_osd_data_template_processing_called(mock_process_templates, tests_tmdata):
    """Test that process_template_mappings is called when process_templates=True."""

    # Mock the template processing function to return modified data
    def mock_template_processing(data, _capability, _template_data):
        # Add mock subarray_templates to the data
        modified_data = data.copy()
        if "AA0.5" in modified_data:
            modified_data["AA0.5"]["subarray_templates"] = {
                "mid_template_1": {"config": "test"}
            }
        return modified_data

    mock_process_templates.side_effect = mock_template_processing

    # Test with process_templates=True
    result, _ = get_osd_data(
        capabilities=["mid"],
        array_assembly="AA0.5",
        tmdata=tests_tmdata,
        process_templates=True,
    )

    # Verify that process_template_mappings was called
    assert mock_process_templates.called

    # Verify the result contains the mocked template data
    assert "capabilities" in result
    assert "mid" in result["capabilities"]
    assert "AA0.5" in result["capabilities"]["mid"]
    assert "subarray_templates" in result["capabilities"]["mid"]["AA0.5"]
    assert (
        "mid_template_1" in result["capabilities"]["mid"]["AA0.5"]["subarray_templates"]
    )


def test_osd_model_accepts_cycle_id_zero():
    """Regression test that OSDModel with cycle_id=0 is valid"""
    model = OSDModel(cycle_id=0)
    assert model.cycle_id == 0


def test_osd_model_fails_cycle_id_zero_and_array_assembly():
    """Regression test that OSDModel with cycle_id=0 and array_assembly raises
    OSDModelError"""
    with pytest.raises(OSDModelError):
        OSDModel(cycle_id=0, array_assembly="AA0.5")
