import json
import logging
import os
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO)


def read_json(json_file_location: str) -> dict[dict[str, Any]]:
    """This function returns json file object from local file system

    :param json_file_location: json file.

    :returns: file content as json object
    """

    cwd = Path(__file__).resolve().parent.parent.parent.parent
    path = os.path.join(cwd, json_file_location)
    with open(path) as user_file:  # pylint: disable=W1514
        file_contents = json.load(user_file)

    return file_contents
