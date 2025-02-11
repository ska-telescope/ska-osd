"""
Functions which the HTTP requests to individual resources are mapped to.

See the operationId fields of the Open API spec for the specific mappings.
"""
import re
from functools import wraps
from http import HTTPStatus
from typing import Dict

from pydantic import ValidationError
from ska_telmodel.data import TMData

from pathlib import Path
from ska_ost_osd.osd.gitlab_helper import push_to_gitlab

from ska_ost_osd.osd.constant import (
    ARRAY_ASSEMBLY_PATTERN,
    LOW_CAPABILITIES_JSON_PATH,
    MID_CAPABILITIES_JSON_PATH,
    OBSERVATORY_POLICIES_JSON_PATH,
    CYCLE_TO_VERSION_MAPPING,
    RELEASE_VERSION_MAPPING,
    osd_file_mapping,
)
from ska_ost_osd.osd.helper import read_json
from ska_ost_osd.osd.osd import get_osd_using_tmdata, update_storage
from ska_ost_osd.osd.osd_schema_validator import OSDModelError
from ska_ost_osd.osd.osd_validation_messages import (
    ARRAY_ASSEMBLY_DOESNOT_EXIST_ERROR_MESSAGE,
    CYCLE_ID_ERROR_MESSAGE,
)
from ska_ost_osd.rest.api.utils import read_file, update_file
from ska_ost_osd.telvalidation import SchematicValidationError, semantic_validate
from ska_ost_osd.telvalidation.constant import (
    CAR_TELMODEL_SOURCE,
    SEMANTIC_VALIDATION_VALUE,
)
from ska_ost_osd.telvalidation.semantic_validator import VALIDATION_STRICTNESS


def error_handler(api_fn: callable) -> str:
    """
    A decorator function to catch general errors and wrap in the correct HTTP response

    :param api_fn: A function which accepts an entity identifier and returns
        an HTTP response

    :return str: A string containing the error message and HTTP status code.
    """

    @wraps(api_fn)
    def wrapper(*args, **kwargs):
        try:
            api_response = api_fn(*args, **kwargs)
            if isinstance(api_response, str):
                return validation_response(
                    status=-1,
                    detail=api_response,
                    http_status=HTTPStatus.BAD_REQUEST,
                    title=HTTPStatus.BAD_REQUEST.phrase,
                )
            return api_response
        except SchematicValidationError as err:
            return validation_response(
                status=0,
                detail=err.args[0].split("\n"),
                title="Semantic Validation Error",
                http_status=HTTPStatus.OK,
            )

        except ValueError as err:
            return validation_response(
                status=-1,
                detail=err.args[0],
                title="Value Error",
                http_status=HTTPStatus.BAD_REQUEST,
            )

        except RuntimeError as err:
            return validation_response(
                status=-1,
                detail=str(err),
                http_status=HTTPStatus.UNPROCESSABLE_ENTITY,
                title=HTTPStatus.UNPROCESSABLE_ENTITY.phrase,
            )

        except Exception as err:  # pylint: disable=W0718
            return validation_response(
                status=-1,
                detail=str(err),
                http_status=HTTPStatus.INTERNAL_SERVER_ERROR,
                title=HTTPStatus.INTERNAL_SERVER_ERROR.phrase,
            )

    return wrapper


@error_handler
def insert_osd_data(body: Dict) -> Dict:
    """
    This function handles REST API requests to insert new OSD data

    Args:
        body (Dict): A dictionary containing the OSD data to insert

    Returns:
        Dict: The processed OSD data

    Raises:
        OSDModelError: If validation fails
        ValueError: If required data is missing or invalid
    """
    try:
        return update_storage(body)
    except (OSDModelError, ValueError) as error:
        raise error


@error_handler
def get_osd(**kwargs) -> dict:
    """This function takes query parameters and OSD data source objects
      to generate a response containing matching OSD data.

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
    """
    Creates an error response in the case that our validation has failed.

    :param detail: The error message if validation fails
    :param http_status: The HTTP status code to return
    :return: HTTP response server error
    """
    response_body = {"status": status, "detail": detail, "title": title}

    return response_body, http_status


def get_tmdata_sources(source):
    return [source] if source else CAR_TELMODEL_SOURCE  # check source


@error_handler
def update_osd_data(body: Dict, **kwargs) -> Dict:
    """
    This function updates the input JSON against the schema

    :param body:
    A dictionary containing key-value pairs of parameters required for validation.

    :returns: :returns dict: A dictionary with OSD data satisfying the query.
    """

    try:
        cycle_id = kwargs.get("cycle_id")
        capabilities = kwargs.get("capabilities")
        array_assembly = kwargs.get("array_assembly")

        if not isinstance(cycle_id, int):
            raise ValueError("Cycle ID must be an integer")

        if capabilities is None:
            raise ValueError("Capabilities must be provided")

        versions_dict = read_json(osd_file_mapping["cycle_to_version_mapping"])
        cycle_ids = [int(key.split("_")[-1]) for key in versions_dict]
        cycle_id_exists = [cycle_id if cycle_id in cycle_ids else None][0]
        string_ids = ",".join([str(i) for i in cycle_ids])

        if cycle_id is not None and cycle_id_exists is None:
            raise ValueError(
                CYCLE_ID_ERROR_MESSAGE.format(cycle_id, string_ids),
            )

        capabilities_path = (
            MID_CAPABILITIES_JSON_PATH
            if capabilities.lower() == "mid"
            else LOW_CAPABILITIES_JSON_PATH
        )

        if array_assembly:
            if not re.match(ARRAY_ASSEMBLY_PATTERN, array_assembly):
                raise ValueError(
                    "Array assembly must be in the format of AA[0-9].[0-9]"
                )

            existing_data = read_file(capabilities_path)
            array_assembly_list = list(
                filter(lambda x: x.startswith("A"), existing_data.keys())
            )

            if array_assembly not in array_assembly_list:
                raise ValueError(
                    ARRAY_ASSEMBLY_DOESNOT_EXIST_ERROR_MESSAGE.format(
                        array_assembly, ", ".join(array_assembly_list)
                    ),
                )

            existing_data[array_assembly].update(body)
            update_file(capabilities_path, existing_data)
            return existing_data

        elif "basic_capabilities" in body.keys():
            existing_data = read_file(capabilities_path)
            existing_data["basic_capabilities"].update(body["basic_capabilities"])
            update_file(capabilities_path, existing_data)
            return existing_data

        elif cycle_id and capabilities:
            existing_data = read_file(OBSERVATORY_POLICIES_JSON_PATH)
            existing_data.update(body)
            update_file(OBSERVATORY_POLICIES_JSON_PATH, existing_data)
            return existing_data

    except (OSDModelError, ValueError) as error:
        raise error
    
@error_handler
def release_osd_data(**kwargs):
    """Release OSD data with automatic version increment based on cycle ID.
    
    Args:
        **kwargs: Keyword arguments including:
            - cycle_id: Required. The cycle ID for version mapping
            - release_type: Optional. Type of release ('major' or 'minor', defaults to patch)
        
    Returns:
        dict: Response containing the new version information
    """
    from ska_ost_osd.osd.version_manager import manage_version_release
    
    cycle_id = kwargs.get('cycle_id')
    if not cycle_id:
        raise ValueError("cycle_id is required")
    cycle_id = "cycle_"+str(cycle_id)
    release_type = kwargs.get('release_type')
    if release_type and release_type not in ['major', 'minor']:
        raise ValueError("release_type must be either 'major' or 'minor' if provided")
    
    # Use version manager to handle version release
    new_version, cycle_id = manage_version_release(cycle_id, release_type)

    files_to_add_small = [
        (Path(LOW_CAPABILITIES_JSON_PATH), osd_file_mapping["low"]),
        (Path(MID_CAPABILITIES_JSON_PATH), osd_file_mapping["mid"]),
        (Path(OBSERVATORY_POLICIES_JSON_PATH), osd_file_mapping["observatory_policies"]),
        (Path(CYCLE_TO_VERSION_MAPPING), "version_mapping/latest_release.txt"),
        (Path(RELEASE_VERSION_MAPPING),osd_file_mapping["cycle_to_version_mapping"]),
    ]
    push_to_gitlab(files_to_add=files_to_add_small,
                   commit_msg="updated tmdata",
                   branch_name="nak-1093-tmdata-push-artifact")
        
    return {
        "status": "success",
        "message": f"Released new version {new_version}",
        "version": str(new_version),
        "cycle_id": cycle_id
    }
    


@error_handler
def semantically_validate_json(body: dict):
    """
    This function validates the input JSON semantically

    :param body:
    A dictionary containing key-value pairs of parameters required for semantic
     validation.
             -observing_command_input: (required) Input JSON to be validated
             -interface: Interface version of the input JSON
             -raise_semantic: (Optional Default True) Raise semantic errors or not
             -sources: (Optional) TMData source URL (gitlab/car) for Semantic Validation
             -osd_data: (Optional) OSD data to be used for semantic validation

    :returns: Flask.Response: A Flask response object that contains the validation
               results. If the validation is successful, the response will indicate
               a success status.
              If the validation fails, the response will include details about the
              semantic errors found. The HTTP status code of the
              response will reflect the outcome of the validation
              (e.g., 200 for success, 400 for bad request if semantic errors
              are detected).

    :raises: SemanticValidationError: If the input JSON is not
             semantically valid semantic and raise semantic is true
    """

    error_details = []

    sources = body.get("sources")
    if sources and not isinstance(sources, str):
        error_details.append("sources must be a string")
    else:
        sources = get_tmdata_sources(sources)

    try:
        tm_data = TMData(sources, update=True)
        semantic_validate(
            observing_command_input=body.get("observing_command_input"),
            tm_data=tm_data,
            raise_semantic=body.get("raise_semantic"),
            interface=body.get("interface"),
            osd_data=body.get("osd_data"),
        )
    except (RuntimeError, ValidationError) as err:
        error_details.extend(handle_validation_error(err))

    if error_details:
        raise ValueError(error_details)

    if int(VALIDATION_STRICTNESS) < int(SEMANTIC_VALIDATION_VALUE):
        return validation_response(
            status=0,
            detail="Semantic Validation is currently disable",
            title="Semantic validation",
            http_status=HTTPStatus.OK,
        )
    else:
        return validation_response(
            status=0,
            detail="JSON is semantically valid",
            title="Semantic validation",
            http_status=HTTPStatus.OK,
        )


def handle_validation_error(err: object) -> list:
    """
    This function handles validation errors and returns a list of error details.
    :param err: error raised from exception
    :returns: List of errors
    """
    if isinstance(err, RuntimeError):
        return [err.args[0]]
    elif isinstance(err, ValidationError):
        return [error["msg"] for error in err.errors()]
