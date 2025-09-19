import json
import os
import pathlib
import tempfile
from functools import partial
from importlib.metadata import version

import pytest
from fastapi.testclient import TestClient
from ska_telmodel.data import TMData

from ska_ost_osd.app import create_app
from ska_ost_osd.osd.osd import osd_tmdata_source
from ska_ost_osd.telvalidation.common.constant import CAR_TELMODEL_SOURCE
from tests.unit.ska_ost_osd.common.constant import (
    DEFAULT_OSD_RESPONSE_WITH_NO_PARAMETER,
    INVALID_MID_CONFIGURE_JSON,
    LOW_ASSIGN_JSON,
    LOW_CAPABILITIES_MOCK_DATA,
    LOW_CONFIGURE_JSON,
    LOW_SBD_JSON,
    LOW_SBD_VALIDATION_MOCK_DATA,
    MID_ASSIGN_JSON,
    MID_CAPABILITIES_MOCK_DATA,
    MID_OSD_DATA_JSON,
    MID_SBD_JSON,
    MID_SBD_VALIDATION_MOCK_DATA,
    VALID_MID_CONFIGURE_JSON,
    VALIDATION_MOCK_DATA,
    local_source,
    low_configure_expected_result_for_invalid_data,
    low_expected_result_for_invalid_data,
    low_sbd_expected_result_for_invalid_data,
    mid_b5_configure_expected_result_for_invalid_data,
    mid_configure_expected_result_for_invalid_data,
    mid_expected_result_for_invalid_data,
    mid_sbd_expected_result_for_invalid_data,
    sources,
)
from tests.unit.ska_ost_osd.utils import create_mock_json_files, read_json

# flake8: noqa E501
# pylint: disable=W0621
OSD_MAJOR_VERSION = version("ska-ost-osd").split(".")[0]
BASE_API_URL = f"/ska-ost-osd/osd/api/v{OSD_MAJOR_VERSION}"


@pytest.fixture(scope="module")
def create_entity_object():
    def _create_entity_object(filepath: str):
        return read_json(filepath)

    return _create_entity_object


@pytest.fixture(scope="session")
def client_get():
    app = create_app()
    client = TestClient(app)

    return partial(client.get, headers={"accept": "application/json"})


@pytest.fixture(scope="session")
def client_put():
    app = create_app()
    client = TestClient(app)

    return partial(client.put)


@pytest.fixture(scope="session")
def client_post():
    app = create_app()
    client = TestClient(app)

    return partial(client.post, headers={"accept": "application/json"})


@pytest.fixture(scope="module")
def git_tm_data():
    return TMData(sources)


# re-defined TMData for local file source
@pytest.fixture(scope="module")
def tm_data():
    return TMData(local_source)


@pytest.fixture
def tmdata_source():
    """TMData source URL fixture."""
    return CAR_TELMODEL_SOURCE


@pytest.fixture(scope="module")
def tm_data_osd(create_entity_object):
    with tempfile.TemporaryDirectory("tmdata") as dirname:
        mid_parent = pathlib.Path(dirname, "ska1_mid")
        mid_parent.mkdir(parents=True)
        create_mock_json_files(
            mid_parent / "mid_capabilities.json",
            create_entity_object(MID_CAPABILITIES_MOCK_DATA),
        )

        low_parent = pathlib.Path(dirname, "ska1_low")
        low_parent.mkdir(parents=True)
        create_mock_json_files(
            low_parent / "low_capabilities.json",
            create_entity_object(LOW_CAPABILITIES_MOCK_DATA),
        )

        create_mock_json_files(
            f"{dirname}/observatory_policies.json",
            create_entity_object(DEFAULT_OSD_RESPONSE_WITH_NO_PARAMETER).get(
                "observatory_policy"
            ),
        )

        mid_validation_parent = pathlib.Path(
            dirname, "instrument", "ska1_mid", "validation"
        )
        mid_validation_parent.mkdir(parents=True)
        create_mock_json_files(
            mid_validation_parent / "mid-validation-constants.json",
            create_entity_object(VALIDATION_MOCK_DATA).get("mid_validation"),
        )

        low_validation_parent = pathlib.Path(
            dirname, "instrument", "ska1_low", "validation"
        )
        low_validation_parent.mkdir(parents=True)
        create_mock_json_files(
            low_validation_parent / "low-validation-constants.json",
            create_entity_object(VALIDATION_MOCK_DATA).get("low_validation"),
        )

        mid_sbd_validation_parent = pathlib.Path(
            dirname, "instrument", "scheduling-block", "validation"
        )
        mid_sbd_validation_parent.mkdir(parents=True)
        create_mock_json_files(
            mid_sbd_validation_parent / "mid_sbd-validation-constants.json",
            create_entity_object(MID_SBD_VALIDATION_MOCK_DATA),
        )

        create_mock_json_files(
            mid_sbd_validation_parent / "low_sbd-validation-constants.json",
            create_entity_object(LOW_SBD_VALIDATION_MOCK_DATA),
        )

        print(f"Dirname: {dirname} {mid_parent} {os.listdir(dirname)}")
        yield TMData([f"file://{dirname}"])


@pytest.fixture(scope="module")
def validate_car_class():
    """This function is used as a fixture for osd_tmdata_source object with
    osd_version as '1.11.0'.

    :returns: osd_tmdata_source object
    """
    tmdata_source, _ = osd_tmdata_source(osd_version="1.11.0")
    return tmdata_source


@pytest.fixture(scope="module")
def validate_gitlab_class():
    """This function is used as a fixture for osd_tmdata_source object with
    parameters.

    :returns: osd_tmdata_source object
    """
    tmdata_source, _ = osd_tmdata_source(
        cycle_id=1,
        gitlab_branch="nak-776-osd-implementation-file-versioning",
        source="gitlab",
    )
    return tmdata_source


@pytest.fixture(scope="module")
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


@pytest.fixture
def mid_osd_data():
    """This fixture returns data in MID_OSD_DATA_JSON file.

    :returns dict: MID_OSD_DATA_JSON file data
    """
    return MID_OSD_DATA_JSON


@pytest.fixture(scope="module")
def mock_mid_data(create_entity_object):
    """This function is used as a fixture for mid json data.

    :returns: mid json data
    """

    return create_entity_object(MID_CAPABILITIES_MOCK_DATA)


@pytest.fixture(scope="module")
def mock_low_data(create_entity_object):
    """This function is used as a fixture for low json data.

    :returns: low json data
    """

    return create_entity_object(LOW_CAPABILITIES_MOCK_DATA)


@pytest.fixture
def valid_observing_command_input(create_entity_object):
    return create_entity_object(MID_ASSIGN_JSON).get("valid")


@pytest.fixture
def invalid_observing_command_input(create_entity_object):
    return create_entity_object(MID_ASSIGN_JSON).get("invalid")


@pytest.fixture(
    scope="module",
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
    scope="module",
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
                    "Cycle 100000 is not valid,Available IDs are 1",
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


@pytest.fixture
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


@pytest.fixture
def valid_semantic_validation_response():
    return {
        "result_data": "JSON is semantically valid",
        "result_status": "success",
        "result_code": 200,
    }


@pytest.fixture
def semantic_validation_disable_response():
    return {
        "result_data": "Semantic Validation is currently disabled",
        "result_status": "success",
        "result_code": 200,
    }


@pytest.fixture
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


@pytest.fixture
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


@pytest.fixture
def observing_command_input_missing_response():
    return {
        "detail": [
            "Value error, [{'field': 'observing_command_input', 'msg': 'This field is"
            " required'}]"
        ],
        "status": -1,
        "title": "Value Error",
    }


@pytest.fixture
def wrong_semantic_validation_parameter_body():
    return {
        "interface": "https://schemka-tmc-assignresources/2.1",
        "raise_semantic": "123",
        "array_assembly": "AA0.5",
        "sources": "car://gitlab.com/ska-telescope14.1#tmdata",
    }


@pytest.fixture
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


@pytest.fixture
def semantic_validation_invalid_array_assembly(valid_observing_command_input):
    return {
        "observing_command_input": valid_observing_command_input,
        "interface": "https://schemka-tmc-assignresources/2.1",
        "raise_semantic": True,
        "array_assembly": "AAA121",
        "sources": "car://gitlab.com/ska-telescope14.1#tmdata",
    }


@pytest.fixture
def valid_only_observing_command_input_in_request_body(valid_observing_command_input):
    return {"observing_command_input": valid_observing_command_input}


@pytest.fixture(
    scope="module",
    params=[
        (MID_ASSIGN_JSON, "valid", "MID", True, False),
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
