"""
Functions which the HTTP requests to individual resources are mapped to.

See the operationId fields of the Open API spec for the specific mappings.
"""
import json
from functools import wraps
from http import HTTPStatus
from os import environ
from pathlib import Path
from typing import Dict

from pydantic import ValidationError
from ska_telmodel.data import TMData

from ska_ost_osd.osd.constant import (
    CYCLE_TO_VERSION_MAPPING,
    MID_CAPABILITIES_JSON_PATH,
    OBSERVATORY_POLICIES_JSON_PATH,
    PUSH_TO_GITLAB_FLAG,
    RELEASE_VERSION_MAPPING,
    osd_file_mapping,
)
from ska_ost_osd.osd.gitlab_helper import push_to_gitlab
from ska_ost_osd.osd.osd import get_osd_using_tmdata, update_file_storage
from ska_ost_osd.osd.osd_schema_validator import CapabilityError, OSDModelError
from ska_ost_osd.osd.osd_update_schema import (
    UpdateRequestModel,
    ValidationOnCapabilities,
)
from ska_ost_osd.osd.osd_validation_messages import (
    ARRAY_ASSEMBLY_DOESNOT_BELONGS_TO_CYCLE_ERROR_MESSAGE,
)
from ska_ost_osd.osd.version_manager import manage_version_release
from ska_ost_osd.rest.api.utils import read_file
from ska_ost_osd.telvalidation import SchematicValidationError, semantic_validate
from ska_ost_osd.telvalidation.constant import (
    CAR_TELMODEL_SOURCE,
    SEMANTIC_VALIDATION_VALUE,
)
from ska_ost_osd.telvalidation.semantic_validator import VALIDATION_STRICTNESS

# this variable is added for restricting tmdata publish from local/dev environment.
# usage: "0" means disable tmdata publish to artefact.
# "1" means allow to publish
PUSH_TO_GITLAB = environ.get("PUSH_TO_GITLAB", "0")


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
        except CapabilityError as err:
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

    Args:
        body (Dict): A dictionary containing key-value pairs of
        parameters required for validation.
        **kwargs: Additional keyword arguments
        including cycle_id and array_assembly

    Returns:
        Dict: A dictionary with OSD data satisfying the query.

    Raises:
        OSDModelError: If validation fails
        ValueError: If data validation or business logic checks fail
    """
    try:
        # Read observatory policies once at the beginning
        osd_data = read_file(OBSERVATORY_POLICIES_JSON_PATH)

        # Prepare input parameters with direct dictionary access
        input_parameters = {
            "cycle_id": kwargs["cycle_id"],
            "array_assembly": kwargs["array_assembly"],
            "capabilities": kwargs["capabilities"],
        }

        # Validate data using Pydantic model
        validated_data = UpdateRequestModel(**input_parameters)

        # Early validation checks
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

        # Combine capability validation with existing data update
        validated_capabilities = ValidationOnCapabilities(**body)
        existing_data = read_file(MID_CAPABILITIES_JSON_PATH)
        return update_file_storage(
            validated_capabilities, body["observatory_policy"], existing_data
        )

    except KeyError as ke:
        raise ValueError(f"Missing required parameter: {ke}") from ke
    except (OSDModelError, ValueError) as error:
        raise error
    except CapabilityError as ce:
        raise ValueError(f"Capability error: {ce}") from ce
    except ValidationError as ve:
        raise ValueError(f"Validation error: {ve}") from ve


@error_handler
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
            branch_name="nak-1089-remove-existing-tmdata-test-7"
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


def get_cycle_list() -> Dict:
    """Get list of cycles from cycle_gitlab_release_version_mapping.json.

    Returns:
        Dict: Dictionary containing list of cycle numbers
    """
    try:
        json_file = "tmdata/version_mapping/cycle_gitlab_release_version_mapping.json"
        with open(json_file, encoding="utf-8") as f:
            data = json.load(f)
        cycle_numbers = []
        for key in data.keys():
            # Extract number from cycle_X format
            if key.startswith("cycle_"):
                try:
                    cycle_num = int(key.split("_")[1])
                    cycle_numbers.append(cycle_num)
                except (IndexError, ValueError):
                    continue

        return {"cycles": sorted(cycle_numbers)}
    except Exception as e:  # pylint: disable=W0718
        return {"error": str(e)}


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
