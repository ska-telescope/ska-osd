import json
import logging
import os
from encodings.punycode import T
from http import HTTPStatus
from pathlib import Path
from typing import Any, Dict, List

from fastapi import status

from ska_ost_osd.common.constant import (
    API_RESPONSE_RESULT_STATUS_FAILED,
    API_RESPONSE_RESULT_STATUS_SUCCESS,
)
from ska_ost_osd.common.models import ApiResponse

logging.basicConfig(level=logging.INFO)


def update_file(filename: Path, json_data: Dict) -> None:
    """Write a dictionary to a JSON file.

    :param filename: The path to the file to be written/updated
    :param json_data: The dictionary to be written to the file
    :returns: None
    :raises: TypeError if json_data is not serializable
    """
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(json_data, file, indent=4)


def read_json(json_file_location: str) -> dict[dict[str, Any]]:
    """This function returns json file object from local file system.

    :param json_file_location: json file.
    :returns: file content as json object
    """

    cwd = Path(__file__).resolve().parent.parent.parent.parent
    path = os.path.join(cwd, json_file_location)
    with open(path) as user_file:  # pylint: disable=W1514
        file_contents = json.load(user_file, parse_float=float)

    return file_contents


def convert_to_response_object(
    response: List[T] | Dict[str, T] | str, result_code: HTTPStatus
) -> ApiResponse:
    """Takes response as argument and returns ApiResponse object :param:
    response: response.

    Returns formatted response object
    """
    result_status = (
        API_RESPONSE_RESULT_STATUS_SUCCESS
        if result_code == HTTPStatus.OK
        else API_RESPONSE_RESULT_STATUS_FAILED
    )

    return ApiResponse(
        result_data=response,
        result_code=result_code,
        result_status=result_status,
    )


def get_responses(response_model) -> Dict[str, Any]:
    """Takes response_model as argument and returns responses dict :param:
    response_model: entity_object.

    Returns formatted response dictionary
    """

    return {
        status.HTTP_200_OK: {
            "description": "Successful Response",
            "model": response_model,
        }
    }


def remove_none_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Takes params dict containing None values.

    Returns filtered params excluding None values
    """
    return {k: v for k, v in params.items() if v is not None}
