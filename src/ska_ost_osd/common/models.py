from http import HTTPStatus
from typing import Dict, Generic, List, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class BaseResponseModel(BaseModel, Generic[T]):
    result_data: List[T] | Dict[str, T] | str
    result_status: str


class ApiResponse(BaseResponseModel[T]):
    result_code: HTTPStatus = HTTPStatus.OK
