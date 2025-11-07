"""Functions which the HTTP requests to individual resources are mapped to.

See the operationId fields of the Open API spec for the specific
mappings.
"""

from http import HTTPStatus
from os import environ
from pathlib import Path
from typing import Dict, Optional

from fastapi import APIRouter, Body, Depends
from pydantic import ValidationError

from ska_ost_osd.common.models import ApiResponse
from ska_ost_osd.common.utils import convert_to_response_object, get_responses
from ska_ost_osd.osd.common.constant import (
    CYCLE_TO_VERSION_MAPPING,
    MID_CAPABILITIES_JSON_PATH,
    RELEASE_VERSION_MAPPING,
    SWAGGER_MID_OSD_DATA_JSON_FILE_PATH,
    osd_file_mapping,
)
from ska_ost_osd.osd.common.error_handling import CapabilityError, OSDModelError
from ska_ost_osd.osd.common.gitlab_helper import push_to_gitlab
from ska_ost_osd.osd.common.utils import (
    get_mid_low_capabilities,
    load_json_from_file,
    read_file,
)
from ska_ost_osd.osd.models.models import (
    CycleModel,
    OSDQueryParams,
    OSDRelease,
    OSDUpdateModel,
    ReleaseType,
    ValidationOnCapabilities,
)
from ska_ost_osd.osd.osd import (
    add_new_data_storage,
    get_osd_using_tmdata,
    update_osd_file,
)
from ska_ost_osd.osd.version_mapping.version_manager import manage_version_release

# this variable is added for restricting tmdata publish from local/dev environment.
# usage: 0 means disable tmdata publish to artefact.
# 1 means allow to publish
PUSH_TO_GITLAB = int(environ.get("PUSH_TO_GITLAB", 0))
osd_router = APIRouter(prefix="")


@osd_router.get(
    "/osd",
    summary="Get OSD data filter by the query parameter",
    description="""Retrieves the OSD cycle_id data which match the query
    parameters. Also requests without parameters will take
    example and default values and return data based on that.
    All query parameters has its own validation if user provide
    any invalid value it will return the error message.
    """,
    responses=get_responses(ApiResponse),
    response_model=ApiResponse,
)
def get_osd(osd_model: OSDQueryParams = Depends()) -> Dict:
    """This function takes query parameters and OSD data source objects to
    generate a response containing matching OSD data.

    :param osd_model (OSDQueryParams): OSD query params model with
        required fields.
    :returns dict: A dictionary with OSD data satisfying the query.
    """
    try:
        model_data = osd_model.model_dump()
        model_data["process_templates"] = True
        osd_data = get_osd_using_tmdata(**model_data)
    except (OSDModelError, ValueError) as error:
        raise error
    return convert_to_response_object(osd_data, result_code=HTTPStatus.OK)


@osd_router.put(
    "/osd",
    summary="Update OSD data filter by the query parameter",
    description="""Update the OSD data which match the query
    parameters. Also requests without parameters will take example
    and default values and return data based on that. All query
    parameters has its own validation if user provide any invalid
    value it will return the error message.
    """,
    responses=get_responses(ApiResponse),
    response_model=ApiResponse,
)
def update_osd_data(
    body: Dict = Body(example=load_json_from_file(SWAGGER_MID_OSD_DATA_JSON_FILE_PATH)),
    osd_model: OSDUpdateModel = Depends(),
) -> Dict:
    """Update the input JSON against the schema.

    :param body: Dict, dictionary containing key-value pairs of
        parameters required for validation.
    :param osd_model: OSDUpdateModel, pydantic model with fields
        cycle_id, array_assembly, and capabilities.
    :return: Dict, dictionary with OSD data satisfying the query.
    :raises ValueError: If data validation or business logic checks
        fail.
    """
    # Handle the simpler case first - when no cycle_id is present
    if osd_model.cycle_id is None:
        return add_new_data_storage(body)

    try:
        # Validate input data
        validated_capabilities = ValidationOnCapabilities(**body)

        existing_data, observatory_policy, telescope = get_mid_low_capabilities(body)

        updated_data = update_osd_file(
            validated_capabilities, observatory_policy, existing_data, telescope
        )
        return convert_to_response_object(updated_data, result_code=HTTPStatus.OK)

    except (ValidationError, KeyError, OSDModelError, CapabilityError) as error:
        raise ValueError(str(error)) from error


@osd_router.post(
    "/osd_release",
    summary="Release new osd version to Gitlab",
    description="Release OSD data with automatic version increment based on cycle ID",
    responses=get_responses(ApiResponse[OSDRelease]),
    response_model=ApiResponse[OSDRelease],
)
def release_osd_data(
    cycle_id: int, release_type: Optional[ReleaseType] = None
) -> ApiResponse[OSDRelease]:
    """Release OSD data with automatic version increment based on cycle ID.

    :param cycle_id: int, the cycle ID for version mapping.
    :param release_type: Optional[ReleaseType], type of release ("major"
        or "minor").
    :return: ApiResponse[OSDRelease], response containing the new
        version information.
    :raises ValueError: If release_type is provided and is not "major"
        or "minor".
    """

    cycle_id = f"cycle_{cycle_id}"

    if release_type and release_type not in ["minor", "major"]:
        raise ValueError("release_type must be either 'major' or 'minor' if provided")

    if not PUSH_TO_GITLAB:
        result = {
            "message": "Push to gitlab is disabled",
            "version": "0.0.0",
            "cycle_id": cycle_id,
        }
        return convert_to_response_object(result, result_code=HTTPStatus.OK)

    # Use version manager to handle version release
    new_version, cycle_id = manage_version_release(cycle_id, release_type)

    files_to_add_small = [
        (Path(MID_CAPABILITIES_JSON_PATH), osd_file_mapping["mid"]),
        (Path(CYCLE_TO_VERSION_MAPPING), "version_mapping/latest_release.txt"),
        (
            Path(RELEASE_VERSION_MAPPING),
            osd_file_mapping["cycle_to_version_mapping"],
        ),
    ]

    push_to_gitlab(
        files_to_add=files_to_add_small,
        commit_msg="updated tmdata",
    )

    result = {
        "message": f"Released new version {new_version}",
        "version": str(new_version),
        "cycle_id": cycle_id,
    }
    return convert_to_response_object(result, result_code=HTTPStatus.OK)


@osd_router.get(
    "/cycle",
    summary="GET list of available proposal cycles",
    description="GET list of all available proposal cycles",
    responses=get_responses(ApiResponse[CycleModel]),
    response_model=ApiResponse,
)
def get_cycle_list() -> ApiResponse[CycleModel]:
    """Get the list of all available proposal cycles.

    :return: ApiResponse[CycleModel], response model containing the list
        of cycle numbers.
    """
    # TODO: instead of relying on RELEASE_VERSION_MAPPING file
    # we should find better approach to find out cycles
    data = read_file(RELEASE_VERSION_MAPPING)

    cycle_numbers = []

    for key in data.keys():
        # Extract number from cycle_X format
        if key.startswith("cycle_"):
            try:
                cycle_num = int(key.split("_")[1])
                cycle_numbers.append(cycle_num)
            except (IndexError, ValueError):
                continue

    cycles = {"cycles": sorted(cycle_numbers)}
    return convert_to_response_object(cycles, result_code=HTTPStatus.OK)


def handle_validation_error(err: object) -> list:
    """Handle validation errors and return a list of error details.

    :param err: object, error raised from an exception.
    :return: list, list of errors.
    """
    if isinstance(err, RuntimeError):
        raise RuntimeError(err.args[0])
    elif isinstance(err, ValidationError):
        raise ValidationError([error["msg"] for error in err.errors()])
