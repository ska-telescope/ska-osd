import json
import os
from typing import Any


class OSDDataException(ValueError):
    """Class to accept the various error messages from OSD module"""

    def __init__(self, message="Undefined error", **_) -> None:
        self.message = message
        super().__init__(self.message)


def read_json(json_file_location: str) -> dict[dict[str, Any]]:

    """This function returns json file object from local file system

    :param json_file_location: json file.

    :returns: file content as json object
    """

    cwd, _ = os.path.split(__file__)
    print("current dir------------", cwd)
    path = os.path.join(cwd, json_file_location)
    print("current dir--path----------", path)
    with open(path) as user_file:
        file_contents = json.load(user_file)

    return file_contents
