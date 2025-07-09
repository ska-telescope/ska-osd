from http import HTTPStatus

from fastapi import Body
from jsonschema import ValidationError
from ska_telmodel.data import TMData

from ska_ost_osd.common.models import ApiResponse
from ska_ost_osd.common.utils import (
    convert_to_response_object,
    get_responses,
    read_json,
)
from ska_ost_osd.osd.routers.api import handle_validation_error, osd_router
from ska_ost_osd.telvalidation.common.constant import (
    CAR_TELMODEL_SOURCE,
    SEMANTIC_VALIDATION_JSON_FILE_PATH,
    SEMANTIC_VALIDATION_VALUE,
)
from ska_ost_osd.telvalidation.common.telvalidation_messages import (
    SEMANTIC_VALIDATION_DISABLED_MSG,
    SEMANTICALLY_VALID_JSON_MSG,
)
from ska_ost_osd.telvalidation.models.semantic_schema_validator import (
    SemanticValidationModel,
)
from ska_ost_osd.telvalidation.semantic_validator import (
    VALIDATION_STRICTNESS,
    semantic_validate,
)


def get_tmdata_sources(source):
    return [source] if source else CAR_TELMODEL_SOURCE  # check source


@osd_router.post(
    "/semantic_validation",
    summary=(
        "Validate input json Semantically Semantic validation checks the"
        " meaning of the input data and ensures that it is valid in the context of"
        " the system. It checks whether the input data conforms to the business rules"
        " and logic of the system"
    ),
    description="Checks if the Command Input JSON is semantically valid",
    responses=get_responses(ApiResponse),
    response_model=ApiResponse,
)
def semantically_validate_json(
    semantic_model: SemanticValidationModel = Body(
        example=read_json(SEMANTIC_VALIDATION_JSON_FILE_PATH)
    ),
):
    """This function validates the input JSON semantically.

    :param body:
    A dictionary containing key-value pairs of parameters required for semantic
     validation.
             -observing_command_input: (required) Input JSON to be validated
             -interface: Interface version of the input JSON
             -raise_semantic: (Optional Default True) Raise semantic errors or not
             -sources: (Optional) TMData source URL (gitlab/car) for Semantic Validation
             -osd_data: (Optional) OSD data to be used for semantic validation

    :returns: response object that contains the validation
               results. If the validation is successful, the response will indicate
               a success status.
              If the validation fails, the response will include details about the
              semantic errors found. The HTTP status code of the
              response will reflect the outcome of the validation
              (e.g., 200 for success, 400 for bad request if semantic errors
              are detected).

    :raises: SemanticValidationError: If the input JSON is not
             semantically valid semantic and raise semantic is true\n
    """

    error_details = []

    sources = semantic_model.sources
    if sources and not isinstance(sources, str):
        error_details.append("sources must be a string")
    else:
        sources = get_tmdata_sources(sources)

    try:
        tm_data = TMData(sources, update=True)
        semantic_validate(
            observing_command_input=semantic_model.observing_command_input,
            tm_data=tm_data,
            raise_semantic=semantic_model.raise_semantic,
            interface=semantic_model.interface,
            osd_data=semantic_model.osd_data,
        )
    except (RuntimeError, ValidationError) as err:
        error_details.extend(handle_validation_error(err))

    if error_details:
        raise ValueError(error_details)

    if int(VALIDATION_STRICTNESS) < int(SEMANTIC_VALIDATION_VALUE):
        return convert_to_response_object(
            response=SEMANTIC_VALIDATION_DISABLED_MSG,
            result_code=HTTPStatus.OK,
        )
    else:
        return convert_to_response_object(
            response=SEMANTICALLY_VALID_JSON_MSG,
            result_code=HTTPStatus.OK,
        )
