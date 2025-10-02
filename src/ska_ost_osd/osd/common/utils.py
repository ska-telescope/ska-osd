import json
import os
from pathlib import Path
from typing import Dict

from ska_telmodel.data import TMData

from ska_ost_osd.osd.common.constant import (
    GITLAB_SOURCE,
    RELEASE_FILE_PATH_LATEST,
)


def load_json_from_file(filename):
    """Load and return the contents of a JSON file located in the parent
    directory of the current script file.

    This function determines the file path by moving two levels up from
    the current script's location and then appending the provided
    filename. It reads the JSON file, parses its content, and returns it
    as a Python object.

    :param filename: str, the name of the JSON file to load.
    :return: Any, the parsed JSON data as a Python object.
    """
    current_file_path = os.path.abspath(__file__)
    parent_dir = os.path.dirname(os.path.dirname(current_file_path))
    file_path = os.path.join(parent_dir, filename)

    with open(file_path, "r", encoding="utf-8") as json_file:
        return json.load(json_file)


def read_file(filename: Path) -> Dict:
    """Read and parse a JSON file into a dictionary.

    :param filename: Path, the path to the JSON file to be read.
    :return: Dict, a dictionary containing the contents of the file.
    :raises FileNotFoundError: If the file does not exist.
    :raises JSONDecodeError: If the file contains invalid JSON.
    """
    with open(filename) as file:  # pylint: disable=W1514
        file_contents = json.load(file, parse_float=float)

    return file_contents


def get_osd_latest_version() -> str:
    """Read the latest_release.txt file and retrieve the latest OSD version.

    :return: str, the latest OSD release version.
    """
    tmdata_version = TMData(GITLAB_SOURCE, update=True)
    osd_version = (
        tmdata_version[RELEASE_FILE_PATH_LATEST].get().decode("utf-8").replace('"', "")
    )

    return osd_version
