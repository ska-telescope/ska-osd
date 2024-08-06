"""
Functions which the HTTP requests to individual resources are mapped to.

See the operationId fields of the Open API spec for the specific mappings.
"""
from functools import wraps
from http import HTTPStatus

from pydantic import ValidationError
from ska_telmodel.data import TMData

from ska_ost_osd.osd.osd import get_osd_using_tmdata
from ska_ost_osd.osd.osd_schema_validator import OSDModelError
from ska_ost_osd.telvalidation import SchematicValidationError, semantic_validate
from ska_ost_osd.telvalidation.constant import CAR_TELMODEL_SOURCE


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

    """
    if isinstance(err, RuntimeError):
        return [err.args[0]]
    elif isinstance(err, ValidationError):
        return [error["msg"] for error in err.errors()]
