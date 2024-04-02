import json
import os
from importlib.metadata import version
from typing import Any

import pytest
from ska_telmodel.data import TMData

from ska_ost_osd.osd.osd import get_osd_data, osd_tmdata_source


def read_json(json_file_location: str) -> dict[dict[str, Any]]:
    """This function returns json file object from local file system

    :param json_file_location: json file.

    :returns: file content as json object
    """

    cwd, _ = os.path.split(__file__)
    path = os.path.join(cwd, json_file_location)

    with open(path) as user_file:  # pylint: disable=W1514
        file_contents = json.load(user_file)

    return file_contents


DEFAULT_OSD_RESPONSE_WITH_NO_PARAMETER = read_json(
    "test_files/default_osd_response.json"
)
OSD_RESPONSE_WITH_ONLY_CAPABILITIES_PARAMETER = read_json(
    "test_files/osd_response_with_capabilities.json"
)
OSD_RESPONSE_WITH_ONLY_ARRAY_ASSEMBLY_PARAMETER = read_json(
    "test_files/osd_response_with_array_assembly.json"
)

file_name = "osd_response_with_capabilities_and_array_assembly.json"
OSD_RESPONSE_WITH_CAPABILITIES_ARRAY_ASSEMBLY_PARAMETER = read_json(
    f"test_files/{file_name}"
)


@pytest.fixture(scope="module")
def tm_data():
    """This function is used as a fixture for tm_data object

    :returns: tmdata object
    """

    source_uris = osd_tmdata_source(cycle_id=1, source="file")
    return TMData(source_uris=source_uris)


@pytest.fixture(scope="module")
def validate_car_class():
    """This function is used as a fixture for osd_tmdata_source object
        with osd_version as '1.11.0'

    :returns: osd_tmdata_source object
    """

    return osd_tmdata_source(osd_version="1.11.0")


@pytest.fixture(scope="module")
def validate_gitlab_class():
    """This function is used as a fixture for osd_tmdata_source object
        with parameters.

    :returns: osd_tmdata_source object
    """

    return osd_tmdata_source(
        cycle_id=1,
        gitlab_branch="nak-776-osd-implementation-file-versioning",
        source="gitlab",
    )


@pytest.mark.parametrize(
    "capabilities, array_assembly, tmdata, expected",
    [
        (None, None, tm_data, DEFAULT_OSD_RESPONSE_WITH_NO_PARAMETER),
        (
            ["mid"],
            None,
            tm_data,
            OSD_RESPONSE_WITH_ONLY_CAPABILITIES_PARAMETER,
        ),
        (
            None,
            "AA0.5",
            tm_data,
            OSD_RESPONSE_WITH_ONLY_ARRAY_ASSEMBLY_PARAMETER,
        ),
        (
            ["mid"],
            "AA0.5",
            tm_data,
            OSD_RESPONSE_WITH_CAPABILITIES_ARRAY_ASSEMBLY_PARAMETER,
        ),
    ],
)
def test_get_osd_data(
    capabilities,
    array_assembly,
    tmdata,  # pylint: disable=W0613
    expected,
    tm_data,  # pylint: disable=W0621
):
    """This test case checks the functionality of get_osd_data
        it converts the python dict into list keys and checks
        for equality with expected output.

    :param capabilities: Mid or Low
    :param array_assembly: Array Assembly AA0.5, AA1
    :param tmdata: tmdata object
    :param expected: output of get_osd_data function
    :param tm_data: tmdata fixture

    :returns: assert equals values
    """

    result = get_osd_data(capabilities, array_assembly, tmdata=tm_data)

    result_keys = list(result["capabilities"].keys())
    expected_keys = list(expected["capabilities"].keys())

    assert result_keys == expected_keys


def test_set_source_car_method(validate_car_class):  # pylint: disable=W0621
    """This test case checks if the output of the osd_tmdata_source
        function is as expected or not.

    :param osd_tmdata_source: validate_car_class fixture.
    """

    assert validate_car_class == (
        "car://gitlab.com/ska-telescope/ost/ska-ost-osd?1.11.0#osd_data",
    )


def test_set_source_gitlab_method(validate_gitlab_class):  # pylint: disable=W0621
    """This test case checks if the output of the osd_tmdata_source
        function is as expected or not.

    :param osd_tmdata_source: validate_gitlab_class fixture.
    """

    msg = "nak-776-osd-implementation-file-versioning#osd_data"

    assert validate_gitlab_class == (
        f"gitlab://gitlab.com/ska-telescope/ost/ska-ost-osd?{msg}",
    )


def test_validate_gitlab_with_both_invalid_param():
    """This test case checks if the output of the osd_tmdata_source
    when no parameter is given and latest version is
    returned or not
    """

    telmodel_version = version("ska_telmodel")

    msg = f"ost/ska-ost-osd?{telmodel_version}#osd_data"

    assert osd_tmdata_source() == (f"car://gitlab.com/ska-telescope/{msg}",)


def test_check_osd_version_method():
    """This test case checks if the output of the osd_tmdata_source
    when osd_version parameter is given it should return the correct URL
    """

    assert osd_tmdata_source(osd_version="1.0.0") == (
        "car://gitlab.com/ska-telescope/ost/ska-ost-osd?1.0.0#osd_data",
    )


def test_check_cycle_id_and_osd_version_method():
    """This test case checks if the output of the osd_tmdata_source
    when cycle_id and osd_version parameter is given
    it should return the correct URL
    """

    msg = "ost/ska-ost-osd?1.11.0#osd_data"

    assert osd_tmdata_source(cycle_id=1, osd_version="1.11.0") == (
        f"car://gitlab.com/ska-telescope/{msg}",
    )


def test_check_cycle_id_2_and_osd_version_method():
    """This test case checks if the output of the osd_tmdata_source
    when cycle_id and osd_version parameter is given
    it should return the correct URL
    """

    assert osd_tmdata_source(cycle_id=2, osd_version="1.0.0") == (
        "car://gitlab.com/ska-telescope/ost/ska-ost-osd?1.0.0#osd_data",
    )


def test_check_cycle_id_with_source_method():
    """This test case checks if the output of the osd_tmdata_source
    when cycle_id, osd_version and source parameter is given
    it should return the correct URL
    """

    assert osd_tmdata_source(cycle_id=2, osd_version="1.0.0", source="file") == (
        "file://osd_data",
    )


def test_check_master_branch_method():
    """This test case checks if the output of the osd_tmdata_source
    when cycle_id, gitlab_branch and source parameter is given
    it should return the correct URL
    """

    assert osd_tmdata_source(cycle_id=2, gitlab_branch="master", source="gitlab") == (
        "gitlab://gitlab.com/ska-telescope/ost/ska-ost-osd?master#osd_data",
    )


def test_invalid_osd_tmdata_source():
    error_msgs = osd_tmdata_source(
        cycle_id=3,
        osd_version="1.1.0",
        gitlab_branch="main",
        source="github",
    )

    expected_error_msg = ", ".join([str(err) for err in error_msgs])
    error_msgs.clear()
    expected_error_msg_1 = "source is not valid available are file, car, gitlab"
    expected_error_msg_2 = (
        "Only one parameter is needed either osd_version or gitlab_branch"
    )
    expected_error_msg_3 = "Cycle id 3 is not valid,Available IDs are 1,2"

    assert (
        expected_error_msg
        == f"{expected_error_msg_1}, {expected_error_msg_2}, {expected_error_msg_3}"
    )


def test_invalid_source():
    error_msgs = osd_tmdata_source(
        cycle_id=1,
        gitlab_branch="main",
        source="file",
    )

    expected_error_msg = ", ".join([str(err) for err in error_msgs])
    error_msgs.clear()

    assert expected_error_msg == "source is not valid."


def test_invalid_get_osd_data_capability(tm_data):  # pylint: disable=W0621
    error_msgs = get_osd_data(
        capabilities=["midd"], array_assembly="AA1", tmdata=tm_data
    )
    expected_error_msg = ", ".join([str(err) for err in error_msgs])
    error_msgs.clear()

    expected_error_msg_1 = (
        "Capability midd doesn't exists,Available are low, mid, observatory_policies"
    )

    assert expected_error_msg == f"{expected_error_msg_1}"


def test_invalid_get_osd_data_array_assembly(tm_data):  # pylint: disable=W0621
    error_msgs = get_osd_data(
        capabilities=["mid"], array_assembly="AA3", tmdata=tm_data
    )

    expected_error_msg = ", ".join([str(err) for err in error_msgs])
    error_msgs.clear()

    expected_error_msg_1 = (
        "Array Assembly AA3 doesn't exists. Available are AA0.5, AA1, AA2"
    )

    assert expected_error_msg == f"{expected_error_msg_1}"
