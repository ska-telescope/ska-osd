from http import HTTPStatus
from typing import Dict, Generic, List, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class BaseResponseModel(BaseModel, Generic[T]):
    """Base response model for API responses.

    This model defines the standard structure for API responses,
    including the result data and the status of the operation.

    :param result_data: List[T] | Dict[str, T] | str, the payload
        containing the result information. Can be a list, dictionary, or
        string.
    :param result_status: str, the status of the result (e.g., "success"
        or "error").
    """

    result_data: List[T] | Dict[str, T] | str
    result_status: str


class ApiResponse(BaseResponseModel[T]):
    """Standardized API response model extending BaseResponseModel.

    This model adds the HTTP status code to the base response fields.

    :param result_code: HTTPStatus, the HTTP status code for the response.
        Defaults to ``HTTPStatus.OK``.
    """

    result_code: HTTPStatus = HTTPStatus.OK
