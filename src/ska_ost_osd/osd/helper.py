import json
import os
from typing import Any


def read_json(json_file_location: str) -> dict[dict[str, Any]]:
    """This function returns json file object from local file system

    :param json_file_location: json file.

    :returns: file content as json object
    """

    cwd, _ = os.path.split(__file__)
    path = os.path.join(cwd, json_file_location)
    with open(path) as user_file:  # pylint: disable=W1514
        file_contents = json.load(user_file, parse_float=float)

    return file_contents
