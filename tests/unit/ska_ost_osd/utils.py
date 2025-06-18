import json
import os
from pathlib import Path
from typing import Dict


def read_json(json_file_location: Path) -> Dict:
    """This function returns json file object from local file system.

    :param json_file_location: json file.
    :returns: file content as json object
    """
    cwd, _ = os.path.split(__file__)
    path = os.path.join(cwd, "routers/", json_file_location)

    with open(path) as user_file:  # pylint: disable=W1514
        file_contents = json.load(user_file)

    return file_contents


def create_mock_json_files(json_file_location: Path, json_data: Dict) -> None:
    """This function create json file for mocking TMData object.

    :param json_file_location: json file.
    :param json_data: json data to be saved.
    :returns: None
    """
    with open(json_file_location, "w") as f:  # pylint: disable=W1514
        json.dump(json_data, f)
