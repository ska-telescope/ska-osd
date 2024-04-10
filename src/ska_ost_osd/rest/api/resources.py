"""
Functions which the HTTP requests to individual resources are mapped to.

See the operationId fields of the Open API spec for the specific mappings.
"""

from functools import wraps
from http import HTTPStatus

from ska_telmodel.data import TMData

from ska_ost_osd.osd.osd import get_osd_data, osd_tmdata_source
from ska_ost_osd.rest.api.query import QueryParams, QueryParamsFactory


def error_handler(api_fn: str) -> str:
    """
    A decorator function to catch general errors and wrap in the correct HTTP response

    :param api_fn: A function which accepts an entity identifier and returns
        an HTTP response
    """

    @wraps(api_fn)
    def wrapper(*args, **kwargs):
        try:
            api_response = api_fn(*args, **kwargs)
            if isinstance(api_response, str):
                return error_response(api_response, HTTPStatus.BAD_REQUEST)
            return api_response

        except RuntimeError as err:
            return error_response(str(err), HTTPStatus.UNPROCESSABLE_ENTITY)

        except ValueError as err:
            return error_response(str(err), HTTPStatus.UNPROCESSABLE_ENTITY)

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

    tm_data, error_msg = osd_tmdata_source(
        cycle_id=query_params.cycle_id,
        osd_version=query_params.osd_version,
        source=query_params.source,
        gitlab_branch=query_params.gitlab_branch,
    )
    if tm_data_sources and error_msg:
        error_msg.extend(tm_data_sources)
        return ", ".join([str(err) for err in error_msg])
    elif error_msg:
        return ", ".join([str(err) for err in error_msg])
    elif tm_data_sources:
        return ", ".join([str(err) for err in tm_data_sources])

    tm_data_src = TMData(source_uris=tm_data)

    osd_data, error_msg_osd_dt = get_osd_data(
        capabilities=[query_params.capabilities],
        tmdata=tm_data_src,
        array_assembly=query_params.array_assembly,
    )

    if error_msg_osd_dt:
        error_msg = ", ".join([str(err) for err in error_msg_osd_dt])
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
    return get_osd_data_response(query_params, error_list.get("err_msg", None))


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
    """

    return QueryParamsFactory.from_dict(kwargs)


def error_response(
    e: Exception, http_status: HTTPStatus = HTTPStatus.INTERNAL_SERVER_ERROR
) -> dict:
    """
    Creates a general server error response from an exception

    :return: HTTP response server error
    """
    response_body = {
        "title": http_status.phrase,
        "detail": f"{e}",
    }

    return response_body, http_status
