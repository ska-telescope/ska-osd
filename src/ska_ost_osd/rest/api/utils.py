import json
from pathlib import Path
from typing import Dict
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def read_file(filename: Path) -> Dict:
    """
    Read and parse a JSON file into a dictionary

    :param filename: The path to the JSON file to be read
    :returns: A dictionary containing the contents of the file
    :raises: FileNotFoundError if file doesn't exist
    :raises: JSONDecodeError if file contains invalid JSON
    """
    with open(filename, "r", encoding="utf-8") as file:
        return json.load(file)


def update_file(filename: Path, json_data: Dict) -> None:
    """
    Write a dictionary to a JSON file

    :param filename: The path to the file to be written/updated
    :param json_data: The dictionary to be written to the file
    :returns: None
    :raises: TypeError if json_data is not serializable
    """
    logger.info("Updating file path for capabilities: %s", filename)
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(json_data, file, indent=4)
