import json
import os


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
