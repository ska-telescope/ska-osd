from http import HTTPStatus
from typing import Dict, Generic, List, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    result_data: List[T] | Dict[str, T] | str
    result_status: str
    result_code: HTTPStatus = HTTPStatus.OK


class ErrorResponseModel(BaseModel, Generic[T]):
    result_data: List[T] | Dict[str, T] | str
    result_status: str
    result_code: HTTPStatus = HTTPStatus.INTERNAL_SERVER_ERROR
