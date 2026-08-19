import json
import os
from importlib.metadata import version

import pytest
from fastapi.testclient import TestClient
from ska_telmodel_client import TMData

from ska_ost_osd.app import create_app
from ska_ost_osd.osd.osd import osd_tmdata_source
from ska_ost_osd.osd.routers.dependencies import (
    get_tmdata_car_main,
    get_tmdata_gitlab_main,
)
from tests.unit.ska_ost_osd.common.constant import (
    INVALID_MID_CONFIGURE_JSON,
    LOW_ASSIGN_JSON,
    LOW_CONFIGURE_JSON,
    LOW_SBD_JSON,
    MID_ASSIGN_JSON,
    MID_ASSIGN_JSON_AA1,
    MID_ASSIGN_JSON_AA2,
    MID_OSD_DATA_JSON,
    MID_OSD_DATA_JSON_AA1,
    MID_OSD_DATA_JSON_AA2,
    MID_SBD_JSON,
    VALID_MID_CONFIGURE_JSON,
    low_configure_expected_result_for_invalid_data,
    low_expected_result_for_invalid_data,
    low_sbd_expected_result_for_invalid_data,
    mid_configure_expected_result_for_invalid_data,
    mid_expected_result_for_invalid_data,
    mid_sbd_expected_result_for_invalid_data,
)
from tests.unit.ska_ost_osd.utils import read_json

# flake8: noqa E501
# pylint: disable=W0621
OSD_MAJOR_VERSION = version("ska-ost-osd").split(".")[0]
BASE_API_URL = f"/ska-ost-osd/osd/api/v{OSD_MAJOR_VERSION}"

# Local tmdata snapshot with version-mapping and latest-release files
TESTS_TMDATA_SOURCE = [f"file://{os.path.join(os.path.dirname(__file__), 'tmdata')}"]


@pytest.fixture(autouse=True)
def patch_tmdata_source(monkeypatch):
    """Patch osd_tmdata_source for all tests so that they use local tmdata"""

    def patched_osd_tmdata_source(*args, **kwargs):
        if "tmdata" not in kwargs:
            kwargs["tmdata"] = TMData(TESTS_TMDATA_SOURCE)
        _, source_error_msg_list = osd_tmdata_source(*args, **kwargs)
        return TESTS_TMDATA_SOURCE, source_error_msg_list

    monkeypatch.setattr(
        "ska_ost_osd.osd.osd.osd_tmdata_source",
        patched_osd_tmdata_source,
    )


@pytest.fixture(scope="session")
def create_entity_object():
    def _create_entity_object(filepath: str):
        return read_json(filepath)

    return _create_entity_object


@pytest.fixture(scope="session")
def test_client(tests_tmdata):
    app = create_app()
    app.dependency_overrides[get_tmdata_car_main] = lambda: tests_tmdata
    app.dependency_overrides[get_tmdata_gitlab_main] = lambda: tests_tmdata
    return TestClient(app)


@pytest.fixture(scope="session")
def empty_client(empty_tmdata):
    app = create_app()
    app.dependency_overrides[get_tmdata_car_main] = lambda: empty_tmdata
    app.dependency_overrides[get_tmdata_gitlab_main] = lambda: empty_tmdata
    return TestClient(app)


@pytest.fixture(scope="session")
def tmdata_source():
    """TMData source URL fixture."""
    return TESTS_TMDATA_SOURCE[0]


@pytest.fixture(scope="session")
def tests_tmdata():
    return TMData(TESTS_TMDATA_SOURCE)


@pytest.fixture(scope="session")
def empty_tmdata(tmp_path_factory):
    """Fixture for an empty TMData instance."""
    empty_dir = tmp_path_factory.mktemp("empty_tmdata")
    return TMData([f"file://{empty_dir}"])


@pytest.fixture(scope="session")
def validate_car_class(tests_tmdata):
    """This function is used as a fixture for osd_tmdata_source object with
    osd_version as '1.11.0'.

    :returns: osd_tmdata_source object
    """
    tmdata_source, _ = osd_tmdata_source(tmdata=tests_tmdata, osd_version="1.11.0")
    return tmdata_source


@pytest.fixture(scope="session")
def validate_gitlab_class(tests_tmdata):
    """This function is used as a fixture for osd_tmdata_source object with
    parameters.

    :returns: osd_tmdata_source object
    """
    tmdata_source, _ = osd_tmdata_source(
        tmdata=tests_tmdata,
        cycle_id=1,
        gitlab_branch="nak-776-osd-implementation-file-versioning",
        source="gitlab",
    )
    return tmdata_source


@pytest.fixture(scope="session")
def osd_versions():
    """This fixture reads a JSON file containing cycle-to-version mappings,
    extracts all unique versions across all cycles, and returns them as a
    sorted list.

    :returns list: A sorted list of unique OSD versions extracted from
        the JSON file.
    """

    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    json_path = os.path.join(
        parent_dir,
        "src",
        "ska_ost_osd",
        "osd",
        "version_mapping",
        "cycle_gitlab_release_version_mapping.json",
    )

    with open(json_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    all_versions = set()
    for cycle_versions in data.values():
        all_versions.update(cycle_versions)

    return sorted(list(all_versions))


@pytest.fixture(scope="session")
def mid_osd_data():
    """This fixture returns data in MID_OSD_DATA_JSON file.

    :returns dict: MID_OSD_DATA_JSON file data
    """
    return MID_OSD_DATA_JSON


@pytest.fixture(scope="session")
def mid_osd_data_aa1():
    """This fixture returns data in MID_OSD_DATA_JSON file.

    :returns dict: MID_OSD_DATA_JSON file data
    """
    return MID_OSD_DATA_JSON_AA1


@pytest.fixture(scope="session")
def mid_osd_data_aa2():
    """This fixture returns data in MID_OSD_DATA_JSON file.

    :returns dict: MID_OSD_DATA_JSON file data
    """
    return MID_OSD_DATA_JSON_AA2


@pytest.fixture(scope="session")
def valid_observing_command_input(create_entity_object):
    return create_entity_object(MID_ASSIGN_JSON).get("valid")


@pytest.fixture(scope="session")
def valid_observing_command_input_aa1(create_entity_object):
    return create_entity_object(MID_ASSIGN_JSON_AA1).get("valid")


@pytest.fixture(scope="session")
def valid_observing_command_input_aa2(create_entity_object):
    return create_entity_object(MID_ASSIGN_JSON_AA2).get("valid")


@pytest.fixture(scope="session")
def invalid_observing_command_input(create_entity_object):
    return create_entity_object(MID_ASSIGN_JSON).get("invalid")


@pytest.fixture(scope="session")
def invalid_observing_command_input_aa1(create_entity_object):
    return create_entity_object(MID_ASSIGN_JSON_AA1).get("invalid")


@pytest.fixture(scope="session")
def invalid_observing_command_input_aa2(create_entity_object):
    return create_entity_object(MID_ASSIGN_JSON_AA2).get("invalid")


@pytest.fixture(
    scope="session",
    params=[
        (
            None,
            "1.0.0",
            "car",
            None,
            "mid",
            "AA0.5",
        ),
        (
            None,
            "1.0.0",
            "car",
            None,
            "low",
            "AA0.5",
        ),
        (
            None,
            None,
            "car",
            None,
            "mid",
            "AA0.5",
        ),
        (
            None,
            None,
            "car",
            None,
            "low",
            "AA0.5",
        ),
        (
            None,
            None,
            "file",
            None,
            "mid",
            "AA0.5",
        ),
        (
            None,
            None,
            "file",
            None,
            "low",
            "AA0.5",
        ),
        (
            None,
            None,
            "car",
            None,
            "low",
            "AA1",
        ),
        (
            None,
            None,
            "file",
            None,
            "mid",
            "AA1",
        ),
        (
            None,
            None,
            "file",
            None,
            "low",
            "AA1",
        ),
        (
            None,
            None,
            "car",
            None,
            "low",
            "AA2",
        ),
        (
            None,
            None,
            "file",
            None,
            "mid",
            "AA2",
        ),
        (
            None,
            None,
            "file",
            None,
            "low",
            "AA2",
        ),
        (
            None,
            None,
            "gitlab",
            "main",
            "mid",
            "AA0.5",
        ),
        (
            None,
            None,
            "gitlab",
            "main",
            "low",
            "AA0.5",
        ),
    ],
)
def mid_low_response_input(request):
    return request.param


@pytest.fixture(
    scope="session",
    params=[
        (
            100000,
            "1..1.0",
            "file",
            "mid",
            "AAA3",
            {
                "result_data": [
                    "Cycle_id and Array_assembly cannot be used together",
                    "osd_version 1..1.0 is not valid",
                    "array_assembly AAA3 is not valid",
                    "Cycle 100000 is not valid,Available IDs are 1,10000",  # need to revisit this
                ],
                "result_status": "failed",
                "result_code": 400,
            },
        ),
        (
            None,
            None,
            "file",
            "mid",
            "AA100000",
            {
                "result_data": [
                    "Array Assembly AA100000 is not valid,Available Array Assemblies"
                    " are AA0.5, AA1, AA2"
                ],
                "result_status": "failed",
                "result_code": 400,
            },
        ),
        (
            1,
            None,
            None,
            None,
            "AA0.5",
            {
                "result_data": ["Cycle_id and Array_assembly cannot be used together"],
                "result_status": "failed",
                "result_code": 400,
            },
        ),
        (
            None,
            None,
            None,
            None,
            None,
            {
                "result_data": ["Either cycle_id or capabilities must be provided"],
                "result_status": "failed",
                "result_code": 400,
            },
        ),
    ],
)
def invalid_osd_tmdata_source_input(request):
    return request.param


@pytest.fixture(scope="session")
def valid_semantic_validation_body(
    tmdata_source, mid_osd_data, valid_observing_command_input
):
    return {
        "observing_command_input": valid_observing_command_input,
        "interface": "https://schema.skao.int/ska-tmc-assignresources/2.1",
        "array_assembly": "AA0.5",
        "sources": tmdata_source,
        "raise_semantic": True,
        "osd_data": mid_osd_data,
    }


@pytest.fixture(scope="session")
def valid_semantic_validation_body_aa1(
    tmdata_source, mid_osd_data_aa1, valid_observing_command_input_aa1
):
    return {
        "observing_command_input": valid_observing_command_input_aa1,
        "interface": "https://schema.skao.int/ska-tmc-assignresources/2.1",
        "array_assembly": "AA1",
        "sources": tmdata_source,
        "raise_semantic": True,
        "osd_data": mid_osd_data_aa1,
    }


@pytest.fixture(scope="session")
def valid_semantic_validation_body_aa2(
    tmdata_source, mid_osd_data_aa2, valid_observing_command_input_aa2
):
    return {
        "observing_command_input": valid_observing_command_input_aa2,
        "interface": "https://schema.skao.int/ska-tmc-assignresources/2.1",
        "array_assembly": "AA2",
        "sources": tmdata_source,
        "raise_semantic": True,
        "osd_data": mid_osd_data_aa2,
    }


@pytest.fixture(scope="session")
def valid_semantic_validation_response():
    return {
        "result_data": "JSON is semantically valid",
        "result_status": "success",
        "result_code": 200,
    }


@pytest.fixture(scope="session")
def semantic_validation_disable_response():
    return {
        "result_data": "Semantic Validation is currently disabled",
        "result_status": "success",
        "result_code": 200,
    }


@pytest.fixture(scope="session")
def invalid_semantic_validation_body(
    tmdata_source, mid_osd_data, invalid_observing_command_input
):
    return {
        "observing_command_input": invalid_observing_command_input,
        "interface": "https://schema.skao.int/ska-tmc-assignresources/2.1",
        "array_assembly": "AA0.5",
        "sources": tmdata_source,
        "raise_semantic": True,
        "osd_data": mid_osd_data,
    }


@pytest.fixture(scope="session")
def invalid_semantic_validation_body_aa1(
    tmdata_source, mid_osd_data_aa1, invalid_observing_command_input_aa1
):
    return {
        "observing_command_input": invalid_observing_command_input_aa1,
        "interface": "https://schema.skao.int/ska-tmc-assignresources/2.1",
        "array_assembly": "AA1",
        "sources": tmdata_source,
        "raise_semantic": True,
        "osd_data": mid_osd_data_aa1,
    }


@pytest.fixture(scope="session")
def invalid_semantic_validation_body_aa2(
    tmdata_source, mid_osd_data_aa2, invalid_observing_command_input_aa2
):
    return {
        "observing_command_input": invalid_observing_command_input_aa2,
        "interface": "https://schema.skao.int/ska-tmc-assignresources/2.1",
        "array_assembly": "AA2",
        "sources": tmdata_source,
        "raise_semantic": True,
        "osd_data": mid_osd_data_aa2,
    }


@pytest.fixture(scope="session")
def invalid_semantic_validation_response():
    return {
        "result_data": [
            "receptor_ids are too many!Current Limit is 4",
            (
                "Invalid input for receptor_ids! Currently allowed ['SKA001',"
                " 'SKA036', 'SKA063', 'SKA100']"
            ),
            "beams are too many! Current limit is 1",
            "Invalid function for beams! Currently allowed visibilities",
            "Invalid input for freq_min",
            "Invalid input for freq_max",
            "freq_min should be less than freq_max",
            "length of receptor_ids should be same as length of receptors",
            "receptor_ids did not match receptors",
        ],
        "result_status": "failed",
        "result_code": 422,
    }


@pytest.fixture(scope="session")
def invalid_semantic_validation_response_aa1():
    return {
        "result_data": [
            "Invalid input for receiver_band! Currently allowed [1,2,5a,5b]",
            "The fsp_ids should all be distinct",
            "Invalid input for channel_width! Currently allowed [13440]",
            "channel_count must be between 1 to 58982",
            "channel_count must be a multiple of 20",
            "Invalid input for start_freq",
            "Invalid input for start_freq",
            "sdp_start_channel_id must be between 0 to 2147483647",
            "integration_factor must be between 1 to 10",
        ],
        "result_status": "failed",
        "result_code": 422,
    }


@pytest.fixture(scope="session")
def invalid_semantic_validation_response_aa2():
    return {
        "result_data": [
            "Invalid input for receiver_band! Currently allowed [1,2,5a,5b]",
            "The fsp_ids should all be distinct",
            (
                "Invalid input for channel_width! Currently allowed [210, 420, 840,"
                " 1680, 3360, 6720, 13440, 26880, 40320, 53760, 80640, 107520, 161280,"
                " 215040, 322560, 416640, 430080, 645120]"
            ),
            "channel_count must be a multiple of 20",
            "Invalid input for start_freq",
            "Invalid input for start_freq",
            "sdp_start_channel_id must be between 0 to 2147483647",
            "integration_factor must be between 1 to 10",
        ],
        "result_status": "failed",
        "result_code": 422,
    }


@pytest.fixture(scope="session")
def observing_command_input_missing_response():
    return {
        "detail": [
            "Value error, [{'field': 'observing_command_input', 'msg': 'This field is"
            " required'}]"
        ],
        "status": -1,
        "title": "Value Error",
    }


@pytest.fixture(scope="session")
def wrong_semantic_validation_parameter_body():
    return {
        "interface": "https://schemka-tmc-assignresources/2.1",
        "raise_semantic": "123",
        "array_assembly": "AA0.5",
        "sources": "car://gitlab.com/ska-telescope14.1#tmdata",
    }


@pytest.fixture(scope="session")
def wrong_semantic_validation_parameter_value_response():
    return {
        "result_data": (
            "Missing field(s): body.observing_command_input. body.raise_semantic: Input"
            " should be a valid boolean, unable to interpret input, invalid payload:"
            " {'interface': 'https://schemka-tmc-assignresources/2.1',"
            " 'raise_semantic': '123', 'array_assembly': 'AA0.5', 'sources':"
            " 'car://gitlab.com/ska-telescope14.1#tmdata'}"
        ),
        "result_status": "failed",
        "result_code": 422,
    }


@pytest.fixture(scope="session")
def semantic_validation_invalid_array_assembly(valid_observing_command_input):
    return {
        "observing_command_input": valid_observing_command_input,
        "interface": "https://schemka-tmc-assignresources/2.1",
        "raise_semantic": True,
        "array_assembly": "AAA121",
        "sources": "car://gitlab.com/ska-telescope14.1#tmdata",
    }


@pytest.fixture(scope="session")
def valid_only_observing_command_input_in_request_body(valid_observing_command_input):
    return {"observing_command_input": valid_observing_command_input}


@pytest.fixture(
    scope="module",
    params=[
        (MID_ASSIGN_JSON, "valid", "MID", True, False),
        (MID_ASSIGN_JSON_AA1, "valid", "MID", True, False),
        (MID_ASSIGN_JSON_AA2, "valid", "MID", True, False),
        (
            MID_ASSIGN_JSON,
            "invalid",
            "MID",
            mid_expected_result_for_invalid_data,
            True,
        ),
        (LOW_ASSIGN_JSON, "valid", "LOW", True, False),
        (
            LOW_ASSIGN_JSON,
            "invalid",
            "LOW",
            low_expected_result_for_invalid_data,
            True,
        ),
        (VALID_MID_CONFIGURE_JSON, "valid", "MID", True, False),
        (
            INVALID_MID_CONFIGURE_JSON,
            "invalid",
            "MID",
            mid_configure_expected_result_for_invalid_data,
            True,
        ),
        (LOW_CONFIGURE_JSON, "valid", "LOW", True, False),
        (
            LOW_CONFIGURE_JSON,
            "invalid",
            "LOW",
            low_configure_expected_result_for_invalid_data,
            True,
        ),
        (MID_SBD_JSON, "valid", "MID", True, False),
        (
            MID_SBD_JSON,
            "invalid",
            "MID",
            mid_sbd_expected_result_for_invalid_data,
            True,
        ),
        (LOW_SBD_JSON, "valid", "LOW", True, False),
        (
            LOW_SBD_JSON,
            "invalid",
            "LOW",
            low_sbd_expected_result_for_invalid_data,
            True,
        ),
        # # Add more test cases here
    ],
)
def semantic_validation_param_input(request):
    return request.param
