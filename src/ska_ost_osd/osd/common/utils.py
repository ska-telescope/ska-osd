import json
import os
from pathlib import Path
from typing import Dict


def load_json_from_file(filename):
    """
    Load and return the contents of a JSON file located in the parent directory
    of the current script file.

    :param filename: Name of the JSON file.
    :return: Parsed JSON data as a Python object.
    """
    current_file_path = os.path.abspath(__file__)
    parent_dir = os.path.dirname(os.path.dirname(current_file_path))
    file_path = os.path.join(parent_dir, filename)

    with open(file_path, "r", encoding="utf-8") as json_file:
        return json.load(json_file)


def read_file(filename: Path) -> Dict:
    """
    Read and parse a JSON file into a dictionary

    :param filename: The path to the JSON file to be read
    :returns: A dictionary containing the contents of the file
    :raises: FileNotFoundError if file doesn't exist
    :raises: JSONDecodeError if file contains invalid JSON
    """
    with open(filename) as file:  # pylint: disable=W1514
        file_contents = json.load(file, parse_float=float)

    return file_contents
