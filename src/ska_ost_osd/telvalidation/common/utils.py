import json
import os
from pathlib import Path
from typing import Any


def read_json(json_file_location: str) -> dict[dict[str, Any]]:
    """Return JSON object loaded from a local file.

    :param json_file_location: str, path to the JSON file.
    :return: dict, file content as a JSON object.
    """

    cwd = Path(__file__).resolve().parent.parent
    path = os.path.join(cwd, json_file_location)
    with open(path) as user_file:  # pylint: disable=W1514
        file_contents = json.load(user_file, parse_float=float)

    return file_contents
