"""Router dependencies for telvalidation endpoints."""

from fastapi import Body, Depends
from ska_telmodel_client import TMData

from ska_ost_osd.osd.common.constant import BASE_FOLDER_NAME, CAR_URL
from ska_ost_osd.telvalidation.common.constant import SWAGGER_SEMANTIC_VALIDATION_JSON_FILE_PATH
from ska_ost_osd.telvalidation.common.utils import read_json
from ska_ost_osd.telvalidation.models.semantic_schema_validator import SemanticValidationModel


def get_semantic_validation_model(
    semantic_model: SemanticValidationModel = Body(
        example=read_json(SWAGGER_SEMANTIC_VALIDATION_JSON_FILE_PATH)
    ),
) -> SemanticValidationModel:
    """Provide validated semantic validation request model."""
    return semantic_model


def get_tmdata_default_semantic_source() -> TMData:
    """Build TMData for default semantic validation source."""
    return TMData([f"car:{CAR_URL}main#{BASE_FOLDER_NAME}"], update=True)


def get_tmdata_for_semantic_validation(
    semantic_model: SemanticValidationModel,
    default_tmdata: TMData,
) -> TMData:
    """Build TMData from request source, or use the default source when omitted."""
    if semantic_model.sources is None:
        return default_tmdata
    return TMData([semantic_model.sources], update=True)


def get_semantic_validation_context(
    semantic_model: SemanticValidationModel = Depends(get_semantic_validation_model),
    tm_data: TMData = Depends(get_tmdata_default_semantic_source),
) -> tuple[SemanticValidationModel, TMData]:
    """Provide both validated request model and corresponding TMData."""
    tm_data = get_tmdata_for_semantic_validation(semantic_model, tm_data)
    return semantic_model, tm_data
