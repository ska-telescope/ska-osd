"""Functions which the HTTP requests to individual resources are mapped to.

See the operationId fields of the Open API spec for the specific
mappings.
"""

from http import HTTPStatus
from os import environ
from pathlib import Path
from typing import Dict

from fastapi import APIRouter
from pydantic import ValidationError

from ska_ost_osd.common.error_handling import CapabilityError, OSDModelError
from ska_ost_osd.common.models import ApiResponse
from ska_ost_osd.common.utils import (
    convert_to_response_object,
    get_responses,
    read_json,
)
from ska_ost_osd.osd.common.constant import (
    CYCLE_TO_VERSION_MAPPING,
    MID_CAPABILITIES_JSON_PATH,
    OBSERVATORY_POLICIES_JSON_PATH,
    PUSH_TO_GITLAB_FLAG,
    RELEASE_VERSION_MAPPING,
    osd_file_mapping,
)
from ska_ost_osd.osd.common.gitlab_helper import push_to_gitlab
from ska_ost_osd.osd.common.osd_validation_messages import (
    ARRAY_ASSEMBLY_DOESNOT_BELONGS_TO_CYCLE_ERROR_MESSAGE,
)
from ska_ost_osd.osd.models.models import (
    CycleModel,
    UpdateRequestModel,
    ValidationOnCapabilities,
)
from ska_ost_osd.osd.osd import (
    add_new_data_storage,
    get_osd_using_tmdata,
    update_file_storage,
)
from ska_ost_osd.osd.version_manager import manage_version_release

# this variable is added for restricting tmdata publish from local/dev environment.
# usage: "0" means disable tmdata publish to artefact.
# "1" means allow to publish
PUSH_TO_GITLAB = environ.get("PUSH_TO_GITLAB", "0")
osd_router = APIRouter(prefix="")


def get_osd(**kwargs) -> dict:
    """This function takes query parameters and OSD data source objects to
    generate a response containing matching OSD data.

    :param query_params (QueryParams): The query parameters.
    :param tm_data_sources (list): A list of OSD data source objects.
    :returns dict: A dictionary with OSD data satisfying the query.
    """
    try:
        cycle_id = kwargs.get("cycle_id")
        osd_version = kwargs.get("osd_version")
        source = kwargs.get("source")
        gitlab_branch = kwargs.get("gitlab_branch")
        capabilities = kwargs.get("capabilities")
        array_assembly = kwargs.get("array_assembly")
        osd_data = get_osd_using_tmdata(
            cycle_id, osd_version, source, gitlab_branch, capabilities, array_assembly
        )
    except (OSDModelError, ValueError) as error:
        raise error
    return osd_data


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


def update_osd_data(body: Dict, **kwargs) -> Dict:
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
    if "cycle_id" not in kwargs:
        return add_new_data_storage(body)

    try:
        # Validate input data
        input_parameters = {
            "cycle_id": kwargs.get("cycle_id"),
            "array_assembly": kwargs.get("array_assembly"),
            "capabilities": kwargs.get("capabilities"),
        }
        validated_data = UpdateRequestModel(**input_parameters)
        validated_capabilities = ValidationOnCapabilities(**body)

        # Check cycle and assembly compatibility if both attributes are present
        if hasattr(validated_data, "cycle_id") and hasattr(
            validated_data, "array_assembly"
        ):
            osd_data = read_json(OBSERVATORY_POLICIES_JSON_PATH)
            if (
                validated_data.cycle_id == osd_data["cycle_number"]
                and validated_data.array_assembly
                != osd_data["telescope_capabilities"]["Mid"]
            ):
                raise CapabilityError(
                    ARRAY_ASSEMBLY_DOESNOT_BELONGS_TO_CYCLE_ERROR_MESSAGE.format(
                        validated_data.array_assembly, validated_data.cycle_id
                    )
                )

        # Update storage with validated data
        existing_data = read_json(MID_CAPABILITIES_JSON_PATH)
        observatory_policy = body.get("observatory_policy", None)

        return update_file_storage(
            validated_capabilities, observatory_policy, existing_data
        )

    except (ValidationError, KeyError, OSDModelError, CapabilityError) as error:
        raise ValueError(str(error)) from error


def release_osd_data(**kwargs):
    """Release OSD data with automatic version increment based on cycle ID.

    Args:
        **kwargs: Keyword arguments including:
            - cycle_id: Required. The cycle ID for version mapping
            - release_type: Optional.
            Type of release ('major' or 'minor', defaults to patch)

    Returns:
        dict: Response containing the new version information
    """
    cycle_id = kwargs.get("cycle_id")
    if not cycle_id:
        raise ValueError("cycle_id is required")
    cycle_id = "cycle_" + str(cycle_id)
    release_type = kwargs.get("release_type")
    # provided support for patch as part of current implementation
    if release_type and release_type not in ["major", "minor"]:
        raise ValueError("release_type must be either 'major' or 'minor' if provided")
    if PUSH_TO_GITLAB == PUSH_TO_GITLAB_FLAG:
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

        return {
            "status": "success",
            "message": f"Released new version {new_version}",
            "version": str(new_version),
            "cycle_id": cycle_id,
        }

    else:
        return {
            "status": "success",
            "message": "Push to gitlab is disabled",
            "version": "0.0.0",
            "cycle_id": cycle_id,
        }


@osd_router.get(
    "/cycle",
    tags=["OSD"],
    summary="GET list of available proposal cycles",
    responses=get_responses(ApiResponse[CycleModel]),
    response_model=ApiResponse[CycleModel],
)
def get_cycle_list() -> Dict:
    """GET list of all available proposal cycles.

    Returns:
        Dict: Dictionary containing list of cycle numbers
    """
    try:
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
    except Exception as e:  # pylint: disable=W0718
        return {"error": str(e)}


def handle_validation_error(err: object) -> list:
    """This function handles validation errors and returns a list of error
    details.

    :param err: error raised from exception
    :returns: List of errors
    """
    if isinstance(err, RuntimeError):
        return [err.args[0]]
    elif isinstance(err, ValidationError):
        return [error["msg"] for error in err.errors()]
