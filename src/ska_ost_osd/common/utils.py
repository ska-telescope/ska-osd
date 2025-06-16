import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

logging.basicConfig(level=logging.INFO)


def read_file(filename: Path) -> Dict:
    """Read and parse a JSON file into a dictionary.

    :param filename: The path to the JSON file to be read
    :returns: A dictionary containing the contents of the file
    :raises: FileNotFoundError if file doesn't exist
    :raises: JSONDecodeError if file contains invalid JSON
    """
    with open(filename, "r", encoding="utf-8") as file:
        return json.load(file)


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
