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

file_name = "osd_response_with_capabilities_and_array_assembly.json"
OSD_RESPONSE_WITH_CAPABILITIES_ARRAY_ASSEMBLY_PARAMETER = read_json(
    f"test_files/{file_name}"
)


@pytest.fixture(scope="module")
def tm_data():
    """This function is used as a fixture for tm_data object

    :returns: tmdata object
    """

    source_uris, _ = osd_tmdata_source(cycle_id=1, source="file")
    return TMData(source_uris=source_uris)


@pytest.fixture(scope="module")
def validate_car_class():
    """This function is used as a fixture for osd_tmdata_source object
        with osd_version as '1.11.0'

    :returns: osd_tmdata_source object
    """
    tmdata_source, _ = osd_tmdata_source(osd_version="1.11.0")
    return tmdata_source


@pytest.fixture(scope="module")
def validate_gitlab_class():
    """This function is used as a fixture for osd_tmdata_source object
        with parameters.

    :returns: osd_tmdata_source object
    """
    tmdata_source, _ = osd_tmdata_source(
        cycle_id=1,
        gitlab_branch="nak-776-osd-implementation-file-versioning",
        source="gitlab",
    )
    return tmdata_source


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

    result, _ = get_osd_data(capabilities, array_assembly, tmdata=tm_data)

    result_keys = list(result["capabilities"].keys())
    expected_keys = list(expected["capabilities"].keys())

    assert result_keys == expected_keys


def test_set_source_car_method(validate_car_class):  # pylint: disable=W0621
    """This test case checks if the output of the osd_tmdata_source
        function is as expected or not.

    :param osd_tmdata_source: validate_car_class fixture.
    """

    assert validate_car_class == ("car:ost/ska-ost-osd?1.11.0#tmdata",)


def test_set_source_gitlab_method(validate_gitlab_class):  # pylint: disable=W0621
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
        cycle_id=3,
        osd_version="1.1.0",
        gitlab_branch="main",
        source="github",
    )
    assert error_msgs == [
        "Source is not valid available are file, car, gitlab",
        "Only one parameter is needed either osd_version or gitlab_branch",
        "Cycle 3 is not valid,Available IDs are 1",
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


def test_invalid_get_osd_data_capability(tm_data):  # pylint: disable=W0621
    """This test case checks if the output of the get_osd_data
    when capabilities is given incorrect with corret array_assembly
    it should return the appropriate error messages.

    :param tm_data: tm_data
    """

    _, error_msgs = get_osd_data(
        capabilities=["midd"], array_assembly="AA1", tmdata=tm_data
    )
    assert error_msgs == [
        "Capability midd is not valid,Available Capabilities are low, mid,"
        " observatory_policies"
    ]


def test_invalid_get_osd_data_array_assembly(tm_data):  # pylint: disable=W0621
    """This test case checks if the output of the get_osd_data
    when array_assembly is given incorrect with corret capabilities
    it should return the appropriate error messages.

    :param tm_data: tm_data
    """

    _, error_msgs = get_osd_data(
        capabilities=["mid"], array_assembly="AA3", tmdata=tm_data
    )
    assert error_msgs == [
        "Array Assembly AA3 is not valid,Available Array Assemblies are AA0.5, AA1, AA2"
    ]
