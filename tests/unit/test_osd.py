import json
import os
from importlib.metadata import version
from typing import Any

import pytest

from ska_telmodel.data import TMData
from ska_telmodel.osd.helper import OSDDataException
from ska_telmodel.osd.osd import get_osd_data, osd_tmdata_source


def read_json(json_file_location: str) -> dict[dict[str, Any]]:

    """This function returns json file object from local file system

    :param json_file_location: json file.

    :returns: file content as json object
    """

    cwd, _ = os.path.split(__file__)
    path = os.path.join(cwd, json_file_location)

    with open(path) as user_file:
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
def test_get_osd_data(capabilities, array_assembly, tmdata, expected, tm_data):

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


def test_invalid_cycle_id_get_osd_data():

    """This test case catches the exception when cycle_id is invalid.

    :raises: OSDDataException for Cycle Id
    """

    with pytest.raises(
        OSDDataException,
        match=("Cycle id 3 is not valid,Available IDs are 1,2"),
    ):
        osd_tmdata_source(cycle_id=3)


def test_invalid_source_get_osd_data():

    """This test case catches the exception when source is invalid.

    :raises: OSDDataException for source value.
    """

    with pytest.raises(
        OSDDataException,
        match=("source is not valid available are file, car, gitlab"),
    ):
        osd_tmdata_source(source="github")


def test_invalid_source_gitlab_branch_get_osd_data():

    """This test case catches the exception when source is not given
        with gitlab_branch parameter.

    :raises: OSDDataException for source value.
    """

    with pytest.raises(
        OSDDataException,
        match=("source is not valid."),
    ):
        osd_tmdata_source(cycle_id=2, gitlab_branch="master")


def test_invalid_capabilities_get_osd_data(tm_data):

    """This test case catches the exception when capabilities is invalid.

    :raises: OSDDataException for capability value.
    """

    msg = "low, mid, observatory_policies"

    with pytest.raises(
        OSDDataException,
        match=(f"Capability midd doesn't exists,Available are {msg}"),
    ):
        get_osd_data(capabilities=["midd"], tmdata=tm_data)


def test_invalid_capabilities_and_valid_array_get_osd_data(tm_data):

    """This test case catches the exception when capabilities is invalid.
        with other parameters

    :raises: OSDDataException for capability value.
    """

    msg = "low, mid, observatory_policies"

    with pytest.raises(
        OSDDataException,
        match=(f"Capability midd doesn't exists,Available are {msg}"),
    ):
        get_osd_data(
            capabilities=["midd"], array_assembly="AA0.5", tmdata=tm_data
        )


def test_invalid_array_assembly(tm_data):

    """This test case catches the exception when array_assembly is invalid.

    :raises: OSDDataException for array_assembly value.
    """

    with pytest.raises(
        OSDDataException,
        match=("Keyerror AA3 doesn't exists"),
    ):
        get_osd_data(array_assembly="AA3", tmdata=tm_data)


def test_set_source_car_method(validate_car_class):

    """This test case checks if the output of the osd_tmdata_source
        function is as expected or not.

    :param osd_tmdata_source: validate_car_class fixture.
    """

    assert validate_car_class == (
        "car://gitlab.com/ska-telescope/ska-telmodel?1.11.0#tmdata",
    )


def test_set_source_gitlab_method(validate_gitlab_class):

    """This test case checks if the output of the osd_tmdata_source
        function is as expected or not.

    :param osd_tmdata_source: validate_gitlab_class fixture.
    """

    msg = "nak-776-osd-implementation-file-versioning#tmdata"

    assert validate_gitlab_class == (
        f"gitlab://gitlab.com/ska-telescope/ska-telmodel?{msg}",
    )


def test_validate_gitlab_with_both_param():

    """This test case catches the exception when both osd_version and
        gitlab_branch are given.

    :raises: OSDDataException
    """

    with pytest.raises(
        OSDDataException,
        match=(
            "Only one parameter is needed either osd_version or gitlab_branch"
        ),
    ):
        osd_tmdata_source(
            cycle_id=1,
            osd_version="1.11.0",
            gitlab_branch="nak-776-osd-implementation-file-versioning",
            source="gitlab",
        )


def test_validate_gitlab_with_both_invalid_param():

    """This test case checks if the output of the osd_tmdata_source
    when no parameter is given and latest version is
    returned or not
    """

    telmodel_version = version("ska_telmodel")

    msg = f"ska-telmodel?{telmodel_version}#tmdata"

    assert osd_tmdata_source() == (f"car://gitlab.com/ska-telescope/{msg}",)


def test_check_osd_version_method():

    """This test case checks if the output of the osd_tmdata_source
    when osd_version parameter is given it should return the correct URL
    """

    assert osd_tmdata_source(osd_version="2.11.0") == (
        "car://gitlab.com/ska-telescope/ska-telmodel?2.11.0#tmdata",
    )


def test_check_cycle_id_and_osd_version_method():

    """This test case checks if the output of the osd_tmdata_source
    when cycle_id and osd_version parameter is given
    it should return the correct URL
    """

    msg = "ska-telmodel?1.11.0#tmdata"

    assert osd_tmdata_source(cycle_id=1, osd_version="1.11.0") == (
        f"car://gitlab.com/ska-telescope/{msg}",
    )


def test_check_cycle_id_2_and_osd_version_method():

    """This test case checks if the output of the osd_tmdata_source
    when cycle_id and osd_version parameter is given
    it should return the correct URL
    """

    assert osd_tmdata_source(cycle_id=2, osd_version="2.11.0") == (
        "car://gitlab.com/ska-telescope/ska-telmodel?2.11.0#tmdata",
    )


def test_check_cycle_id_with_source_method():

    """This test case checks if the output of the osd_tmdata_source
    when cycle_id, osd_version and source parameter is given
    it should return the correct URL
    """

    assert osd_tmdata_source(
        cycle_id=2, osd_version="2.11.0", source="file"
    ) == ("file://tmdata",)


def test_check_master_branch_method():

    """This test case checks if the output of the osd_tmdata_source
    when cycle_id, gitlab_branch and source parameter is given
    it should return the correct URL
    """

    assert osd_tmdata_source(
        cycle_id=2, gitlab_branch="master", source="gitlab"
    ) == ("gitlab://gitlab.com/ska-telescope/ska-telmodel?master#tmdata",)
