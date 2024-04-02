"""
Functions which the HTTP requests to individual resources are mapped to.

See the operationId fields of the Open API spec for the specific mappings.
"""

import logging
from functools import wraps
from http import HTTPStatus

from ska_telmodel.data import TMData

from ska_oso_osd.osd.helper import OSDDataException
from ska_oso_osd.osd.osd import get_osd_data, osd_tmdata_source
from ska_oso_osd.rest.api.query import QueryParams, QueryParamsFactory

LOGGER = logging.getLogger(__name__)


def error_handler(api_fn: str) -> str:
    """
    A decorator function to catch general errors and wrap in the correct HTTP response

    :param api_fn: A function which accepts an entity identifier and returns
        an HTTP response
    """

    @wraps(api_fn)
    def wrapper(*args, **kwargs):
        try:
            return api_fn(*args, **kwargs)
        except OSDDataException as err:
            return (
                validation_response(err.args[0], HTTPStatus.BAD_REQUEST),
                HTTPStatus.BAD_REQUEST,
            )
        except ValueError as err:
            return (
                validation_response(err.args[0], HTTPStatus.BAD_REQUEST),
                HTTPStatus.BAD_REQUEST,
            )
        except Exception as err:  # pylint: disable=W0718
            return validation_response(str(err)), HTTPStatus.INTERNAL_SERVER_ERROR

    return wrapper


@error_handler
def get_osd_data_response(query_params, tm_data_sources):
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

    tm_data = TMData(source_uris=tm_data_sources, update=True)

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
    query_params, error_list = get_qry_params(kwargs)

    return get_osd_data_response(query_params, error_list)


def validation_response(
    error_msg: str, http_status: HTTPStatus = HTTPStatus.UNPROCESSABLE_ENTITY
):
    """
    Creates an error response in the case that our validation has failed.
    """
    response_body = {"Error": error_msg}

    return response_body, http_status


def get_qry_params(kwargs: dict) -> QueryParams:
    """
    Convert the parameters from the request into QueryParams.

    Currently only a single instance of QueryParams is supported, so
    subsequent parameters will be ignored.

    :param kwargs: Dict with parameters from HTTP GET request
    :return: An instance of QueryParams
    :raises: TypeError if a supported QueryParams cannot be extracted
    """

    return QueryParamsFactory.from_dict(kwargs)
