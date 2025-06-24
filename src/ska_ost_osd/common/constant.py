from fastapi import status
from fastapi.exceptions import ResponseValidationError

API_RESPONSE_RESULT_STATUS_SUCCESS = "success"
API_RESPONSE_RESULT_STATUS_FAILED = "failed"

EXCEPTION_STATUS_MAP = {
    FileNotFoundError: status.HTTP_404_NOT_FOUND,
    ResponseValidationError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ValueError: status.HTTP_400_BAD_REQUEST,
    KeyError: status.HTTP_400_BAD_REQUEST,
    TypeError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    Exception: status.HTTP_500_INTERNAL_SERVER_ERROR,
}
