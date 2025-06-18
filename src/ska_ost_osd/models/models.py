from http import HTTPStatus
from typing import Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

from ska_ost_osd.osd.constant import ARRAY_ASSEMBLY_PATTERN

T = TypeVar("T")


class UpdateRequestModel(BaseModel):
    cycle_id: Optional[int] = Field(..., description="Cycle ID must be an integer")
    array_assembly: Optional[str] = Field(
        ...,
        pattern=ARRAY_ASSEMBLY_PATTERN,
        description="Array assembly in format AA[0-9].[0-9]",
    )
    capabilities: Optional[str] = Field(..., description="Capabilities must be str")


class ApiResponse(BaseModel, Generic[T]):
    result_data: List[T] | Dict[str, T] | str
    result_status: str
    result_code: HTTPStatus = HTTPStatus.OK


class CycleModel(BaseModel):
    cycles: List[int]


class ErrorResponseModel(BaseModel, Generic[T]):
    result_data: List[T] | Dict[str, T] | str
    result_status: str
    result_code: HTTPStatus = HTTPStatus.INTERNAL_SERVER_ERROR
