"""
Functions which the HTTP requests to individual resources are mapped to.

See the operationId fields of the Open API spec for the specific mappings.
"""

import logging
import re
from functools import wraps
from http import HTTPStatus
from importlib.metadata import version

from ska_telmodel.data import TMData

from ska_ost_osd.osd.osd import get_osd_data, osd_tmdata_source
from ska_ost_osd.rest.api.query import QueryParams, QueryParamsFactory
from ska_ost_osd.telvalidation import SchematicValidationError, semantic_validate

LOGGER = logging.getLogger(__name__)

TELMODEL_LIB_VERSION = version("ska_telmodel")
CAR_TELMODEL_SOURCE = (
    f"car://gitlab.com/ska-telescope/ska-telmodel?{TELMODEL_LIB_VERSION}#tmdata",
)


def error_handler(api_fn: callable) -> str:
    """
    A decorator function to catch general errors and wrap in the correct HTTP response

    :param api_fn: A function which accepts an entity identifier and returns
        an HTTP response
    """

    @wraps(api_fn)
    def wrapper(*args, **kwargs):
        try:
            return api_fn(*args, **kwargs)
        except SchematicValidationError as err:
            return (
                validation_response(
                    status=0,
                    error_msg=err.args[0].split("\n"),
                    title="Semantic Validation Error",
                    http_status=HTTPStatus.OK,
                ),
                HTTPStatus.OK,
            )
        except ValueError as err:
            return (
                validation_response(
                    status=-1,
                    error_msg=err.args[0],
                    title="Value Error",
                    http_status=HTTPStatus.BAD_REQUEST,
                ),
                HTTPStatus.BAD_REQUEST,
            )
        except Exception as err:  # pylint: disable=W0718
            return validation_response(str(err)), HTTPStatus.INTERNAL_SERVER_ERROR

    return wrapper


@error_handler
def get_osd_data_response(query_params, tm_data_sources):
    """This function takes query parameters and OSd data source objects
      to generate a response containing matching OSd data.

    :param query_params (QueryParams): The query parameters.
    :param tm_data_sources (list): A list of OSd data source objects.

    :returns dict: A dictionary with OSd data satisfying the query.
    """

    tm_data_sources = osd_tmdata_source(
        cycle_id=query_params.cycle_id,
        osd_version=query_params.osd_version,
        source=query_params.source,
        gitlab_branch=query_params.gitlab_branch,
    )

    if isinstance(tm_data_sources, list):
        error_msg = ", ".join([str(err) for err in tm_data_sources])
        tm_data_sources.clear()
        return error_msg

    tm_data = TMData(source_uris=tm_data_sources)

    osd_data = get_osd_data(
        capabilities=[query_params.capabilities],
        tmdata=tm_data,
        array_assembly=query_params.array_assembly,
    )

    if isinstance(osd_data, list):
        error_msg = ", ".join([str(err.message) for err in osd_data])
        osd_data.clear()
        return error_msg

    return osd_data


@error_handler
def get_osd(**kwargs):
    """This function retrieves OSD resources based on the parameters passed.

    :param kwargs (dict): Additional keyword arguments to filter results.
    :returns dict/list: The matching OSD resources.
    :raises ValueError: If invalid parameters are passed.
    """

    query_params, error_list = get_qry_params(kwargs)

    return get_osd_data_response(query_params, error_list)


def validation_response(
    error_msg: str,
    status: int = 0,
    title: str = "Below Error have occoured kindly check",
    http_status: HTTPStatus = HTTPStatus.UNPROCESSABLE_ENTITY,
):
    """
    Creates an error response in the case that our validation has failed.
    """
    response_body = {"detail": error_msg, "title": title, "status": status}

    return response_body, http_status


def get_qry_params(kwargs: dict) -> QueryParams:
    """
    Convert the parameters from the request into QueryParams.

    Currently only a single instance of QueryParams is supported, so
    subsequent parameters will be ignored.

    :param kwargs: Dict with parameters from HTTP GET request
    :return: An instance of QueryParams
    """

    return QueryParamsFactory.from_dict(kwargs)


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
             -sources: (Optional) TMData source
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
    error_details = {}
    observing_command_input = body.get("observing_command_input")
    if observing_command_input is None:
        error_details["observing_command_output"] = "observing_command_input is missing"

    interface: str = body.get("interface")  # check if interface is None
    if interface:
        pattern = r"^https://schema\.skao\.int/[a-zA-Z-]+/\d+\.\d+$"
        if not re.match(pattern, interface):
            error_details["interface"] = "interface is not valid"

    raise_semantic: bool = body.get("raise_semantic")  # True
    if raise_semantic and not isinstance(raise_semantic, bool):
        error_details["raise_semantic"] = "raise_semantic is not a boolean value "

    sources = (
        [body.get("sources")] if body.get("sources") else CAR_TELMODEL_SOURCE
    )  # check source
    tm_data = {}

    try:
        tm_data = TMData(sources)
    except RuntimeError as err:
        error_details["sources"] = err.args[0]

    osd_data = body.get("osd_data")
    if error_details:
        raise ValueError(error_details)

    print(
        "semantic_validate func output:",
        semantic_validate(
            observing_command_input=observing_command_input,
            tm_data=tm_data,
            raise_semantic=raise_semantic,
            interface=interface,
            osd_data=osd_data,
        ),
    )
    return {
        "status": 0,
        "details": "JSON is semantically valid",
        "title": "Semantic validation",
    }, HTTPStatus.OK
