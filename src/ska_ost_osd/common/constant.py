from fastapi import status
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from gitlab import GitlabGetError

API_RESPONSE_RESULT_STATUS_SUCCESS = "success"
API_RESPONSE_RESULT_STATUS_FAILED = "failed"

EXCEPTION_STATUS_MAP = {
    FileNotFoundError: status.HTTP_404_NOT_FOUND,
    ResponseValidationError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ValueError: status.HTTP_400_BAD_REQUEST,
    KeyError: status.HTTP_400_BAD_REQUEST,
    TypeError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    Exception: status.HTTP_500_INTERNAL_SERVER_ERROR,
    RequestValidationError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    GitlabGetError: status.HTTP_404_NOT_FOUND,
}
# EXCEPTION_STATUS_MAP = {
#     (FileNotFoundError, GitlabGetError): status.HTTP_404_NOT_FOUND,
#     (ValueError, KeyError): status.HTTP_400_BAD_REQUEST,
#     (TypeError, RequestValidationError): status.HTTP_422_UNPROCESSABLE_ENTITY,
#     (ResponseValidationError, Exception): status.HTTP_500_INTERNAL_SERVER_ERROR,
# }
