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
    INVALID_MID_ASSIGN_JSON,
    LOW_MOCK_DATA,
    LOW_SBD_VALIDATION_MOCK_DATA,
    LOW_VALIDATION_MOCK_DATA,
    MID_MOCK_DATA,
    MID_OSD_DATA_JSON,
    MID_SBD_VALIDATION_MOCK_DATA,
    MID_VALIDATION_MOCK_DATA,
    OBSERVATORY_MOCK_DATA,
    VALID_MID_ASSIGN_JSON,
    local_source,
    sources,
)
from tests.unit.ska_ost_osd.utils import create_mock_json_files

# flake8: noqa E501
# pylint: disable=W0621
OSD_MAJOR_VERSION = version("ska-ost-osd").split(".")[0]
BASE_API_URL = f"/ska-ost-osd/osd/api/v{OSD_MAJOR_VERSION}"


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
    return CAR_TELMODEL_SOURCE[0]


@pytest.fixture(scope="module")
def tm_data_osd():
    with tempfile.TemporaryDirectory("tmdata") as dirname:
        mid_parent = pathlib.Path(dirname, "ska1_mid")
        mid_parent.mkdir(parents=True)
        create_mock_json_files(mid_parent / "mid_capabilities.json", MID_MOCK_DATA)

        low_parent = pathlib.Path(dirname, "ska1_low")
        low_parent.mkdir(parents=True)
        create_mock_json_files(low_parent / "low_capabilities.json", LOW_MOCK_DATA)

        create_mock_json_files(
            f"{dirname}/observatory_policies.json", OBSERVATORY_MOCK_DATA
        )

        mid_validation_parent = pathlib.Path(
            dirname, "instrument", "ska1_mid", "validation"
        )
        mid_validation_parent.mkdir(parents=True)
        create_mock_json_files(
            mid_validation_parent / "mid-validation-constants.json",
            MID_VALIDATION_MOCK_DATA,
        )

        low_validation_parent = pathlib.Path(
            dirname, "instrument", "ska1_low", "validation"
        )
        low_validation_parent.mkdir(parents=True)
        create_mock_json_files(
            low_validation_parent / "low-validation-constants.json",
            LOW_VALIDATION_MOCK_DATA,
        )

        mid_sbd_validation_parent = pathlib.Path(
            dirname, "instrument", "scheduling-block", "validation"
        )
        mid_sbd_validation_parent.mkdir(parents=True)
        create_mock_json_files(
            mid_sbd_validation_parent / "mid_sbd-validation-constants.json",
            MID_SBD_VALIDATION_MOCK_DATA,
        )

        create_mock_json_files(
            mid_sbd_validation_parent / "low_sbd-validation-constants.json",
            LOW_SBD_VALIDATION_MOCK_DATA,
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


@pytest.fixture
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


@pytest.fixture
def osd_observatory_policies():
    """This fixture returns data in OBSERVATORY_MOCK_DATA file.

    :returns dict: OBSERVATORY_MOCK_DATA file data
    """
    return OBSERVATORY_MOCK_DATA


@pytest.fixture(scope="module")
def mock_mid_data():
    """This function is used as a fixture for mid json data.

    :returns: mid json data
    """

    return MID_MOCK_DATA


@pytest.fixture(scope="module")
def mock_low_data():
    """This function is used as a fixture for low json data.

    :returns: low json data
    """

    return LOW_MOCK_DATA


@pytest.fixture
def valid_observing_command_input():
    return VALID_MID_ASSIGN_JSON


@pytest.fixture
def invalid_observing_command_input():
    return INVALID_MID_ASSIGN_JSON


@pytest.fixture
def valid_semantic_validation_body(
    tmdata_source, mid_osd_data, valid_observing_command_input
):
    return {
        "observing_command_input": valid_observing_command_input,
        "interface": "https://schema.skao.int/ska-tmc-assignresources/2.1",
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
        "result_data": "Semantic Validation is currently disable",
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
        "sources": tmdata_source,
        "raise_semantic": True,
        "osd_data": mid_osd_data,
    }


@pytest.fixture
def invalid_semantic_validation_response():
    return {
        "result_data": [
            [
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
            ]
        ],
        "result_status": "success",
        "result_code": 200,
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
        "sources": "car://gitlab.com/ska-telescope14.1#tmdata",
    }


@pytest.fixture
def wrong_semantic_validation_parameter_value_response():
    return {
        "result_data": (
            "Missing field(s): body.observing_command_input. body.raise_semantic: Input"
            " should be a valid boolean, unable to interpret input, invalid payload:"
            " {'interface': 'https://schemka-tmc-assignresources/2.1',"
            " 'raise_semantic': '123', 'sources':"
            " 'car://gitlab.com/ska-telescope14.1#tmdata'}"
        ),
        "result_status": "failed",
        "result_code": 422,
    }


@pytest.fixture
def valid_only_observing_command_input_in_request_body(valid_observing_command_input):
    return {"observing_command_input": valid_observing_command_input}
