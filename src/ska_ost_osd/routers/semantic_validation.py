from http import HTTPStatus

from jsonschema import ValidationError
from ska_telmodel.data import TMData

from ska_ost_osd.common.constant import CAR_TELMODEL_SOURCE, SEMANTIC_VALIDATION_VALUE
from ska_ost_osd.routers.osd_api import (
    error_handler,
    handle_validation_error,
    validation_response,
)
from ska_ost_osd.telvalidation.semantic_validator import (
    VALIDATION_STRICTNESS,
    semantic_validate,
)


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
