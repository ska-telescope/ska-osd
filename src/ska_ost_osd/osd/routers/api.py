"""Functions which the HTTP requests to individual resources are mapped to.

See the operationId fields of the Open API spec for the specific
mappings.
"""

from http import HTTPStatus
from os import environ
from pathlib import Path
from typing import Dict

from fastapi import APIRouter, Body, Depends
from pydantic import ValidationError

from ska_ost_osd.common.models import ApiResponse
from ska_ost_osd.common.utils import (
    convert_to_response_object,
    get_responses,
    read_json,
)
from ska_ost_osd.osd.common.constant import (
    CYCLE_TO_VERSION_MAPPING,
    MID_CAPABILITIES_JSON_PATH,
    MID_OSD_DATA_JSON_FILE_PATH,
    OBSERVATORY_POLICIES_JSON_PATH,
    RELEASE_VERSION_MAPPING,
    osd_file_mapping,
)
from ska_ost_osd.osd.common.error_handling import CapabilityError, OSDModelError
from ska_ost_osd.osd.common.gitlab_helper import push_to_gitlab
from ska_ost_osd.osd.common.osd_validation_messages import (
    ARRAY_ASSEMBLY_DOESNOT_BELONGS_TO_CYCLE_ERROR_MESSAGE,
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
    update_file_storage,
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

    :param query_params (QueryParams): The query parameters.
    :param tm_data_sources (list): A list of OSD data source objects.
    :returns dict: A dictionary with OSD data satisfying the query.
    """
    try:
        cycle_id = osd_model.cycle_id
        osd_version = osd_model.osd_version
        source = osd_model.source
        gitlab_branch = osd_model.gitlab_branch
        capabilities = osd_model.capabilities
        array_assembly = osd_model.array_assembly
        osd_data = get_osd_using_tmdata(
            cycle_id, osd_version, source, gitlab_branch, capabilities, array_assembly
        )
    except (OSDModelError, ValueError) as error:
        raise error
    return convert_to_response_object(osd_data, result_code=HTTPStatus.OK)


def validation_response(
    detail: str,
    status: int = 0,
    title: str = HTTPStatus.INTERNAL_SERVER_ERROR.phrase,
    http_status: HTTPStatus = HTTPStatus.INTERNAL_SERVER_ERROR,
) -> dict:
    """Creates an error response in the case that our validation has failed.

    :param detail: The error message if validation fails
    :param http_status: The HTTP status code to return
    :return: HTTP response server error
    """
    response_body = {"status": status, "detail": detail, "title": title}

    return response_body, http_status


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
    body: Dict = Body(example=read_json(MID_OSD_DATA_JSON_FILE_PATH)),
    osd_model: OSDUpdateModel = Depends(),
) -> Dict:
    """This function updates the input JSON against the schema.

    Args:
        body (Dict): A dictionary containing key-value pairs of
        parameters required for validation.
        **kwargs: Additional keyword arguments
        including cycle_id and array_assembly

    Returns:
        Dict: A dictionary with OSD data satisfying the query.

    Raises:
        ValueError: If data validation or business logic checks fail
    """
    # Handle the simpler case first - when no cycle_id is present
    if not osd_model.cycle_id:
        return add_new_data_storage(body)

    try:
        # Validate input data
        input_parameters = {
            "cycle_id": osd_model.cycle_id,
            "array_assembly": osd_model.array_assembly,
            "capabilities": osd_model.capabilities,
        }
        validated_data = OSDUpdateModel(**input_parameters)
        validated_capabilities = ValidationOnCapabilities(**body)

        # Check cycle and assembly compatibility if both attributes are present
        if hasattr(validated_data, "cycle_id") and hasattr(
            validated_data, "array_assembly"
        ):
            osd_model = read_json(OBSERVATORY_POLICIES_JSON_PATH)
            if (
                validated_data.cycle_id == osd_model["cycle_number"]
                and validated_data.array_assembly
                != osd_model["telescope_capabilities"]["Mid"]
            ):
                raise CapabilityError(
                    ARRAY_ASSEMBLY_DOESNOT_BELONGS_TO_CYCLE_ERROR_MESSAGE.format(
                        validated_data.array_assembly, validated_data.cycle_id
                    )
                )

        # Update storage with validated data
        existing_data = read_json(MID_CAPABILITIES_JSON_PATH)
        observatory_policy = body.get("observatory_policy", None)

        updated_data = update_file_storage(
            validated_capabilities, observatory_policy, existing_data
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
    cycle_id: int, release_type: ReleaseType
) -> ApiResponse[OSDRelease]:
    """Release OSD data with automatic version increment based on cycle ID.

    Args:
        - cycle_id: Required. The cycle ID for version mapping
        - release_type: Required. Type of release ('major' or 'minor')

    Returns:
        ApiResponse[OSDRelease]: Response containing the new version information
    """

    cycle_id = f"cycle_{cycle_id}"

    if release_type not in ["minor", "major"]:
        raise ValueError("release_type must be either 'major' or 'minor' if provided")

    if PUSH_TO_GITLAB:
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

    else:
        result = {
            "message": "Push to gitlab is disabled",
            "version": "0.0.0",
            "cycle_id": cycle_id,
        }
        return convert_to_response_object(result, result_code=HTTPStatus.OK)


@osd_router.get(
    "/cycle",
    summary="GET list of available proposal cycles",
    description="GET list of all available proposal cycles",
    responses=get_responses(ApiResponse[CycleModel]),
    response_model=ApiResponse[CycleModel],
)
def get_cycle_list() -> ApiResponse[CycleModel]:
    """GET list of all available proposal cycles.

    Returns:
        ApiResponse[CycleModel]: Response model containing list of cycle numbers
    """
    # TODO: instead of relying on RELEASE_VERSION_MAPPING file
    # we should find better approach to find out cycles
    data = read_json(RELEASE_VERSION_MAPPING)

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
    """This function handles validation errors and returns a list of error
    details.

    :param err: error raised from exception
    :returns: List of errors
    """
    if isinstance(err, RuntimeError):
        raise RuntimeError(err.args[0])
    elif isinstance(err, ValidationError):
        raise ValidationError([error["msg"] for error in err.errors()])
