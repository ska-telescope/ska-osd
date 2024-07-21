"""
This module contains the 'semantic_validate' functions which is exposed
to outside for use. If observing command's input contains invalid
values it will raise validation error's based on provided rules.
Integrated OSD API function to fetch rule constraints values.
"""


import logging
from typing import Any, Dict, List, Optional, Tuple

from ska_telmodel.data import TMData

from .constant import (
    LOW_VALIDATION_CONSTANT_JSON_FILE_PATH,
    MID_VALIDATION_CONSTANT_JSON_FILE_PATH,
    SBD_VALIDATION_CONSTANT_JSON_FILE_PATH,
    SKA_LOW_TELESCOPE,
    SKA_MID_TELESCOPE,
    SKA_SBD,
)
from .oet_tmc_validators import validate_json
from .schematic_validation_exceptions import SchematicValidationError

logging.getLogger("telvalidation")


def get_validation_data(interface: str) -> Optional[str]:
    """
    Get the validation constant JSON file path based on the provided interface URI.

    :param interface: str, the interface URI from the observing command input.
    :return: str, the validation constant JSON file path, or None if not found.
    """
    validation_constants = {
        SKA_LOW_TELESCOPE: LOW_VALIDATION_CONSTANT_JSON_FILE_PATH,
        SKA_MID_TELESCOPE: MID_VALIDATION_CONSTANT_JSON_FILE_PATH,
        SKA_SBD: SBD_VALIDATION_CONSTANT_JSON_FILE_PATH,
    }

    for key, value in validation_constants.items():
        if key in interface:
            return value
    # taking mid interface as default cause there is no any specific
    # key to differentiate the interface
    return validation_constants.get(SKA_MID_TELESCOPE)


def fetch_capabilities_from_osd(
    telescope: str,
    array_assembly: str,
    tm_data: Optional[Dict] = None,
    osd_data: Optional[Dict] = None,
) -> Tuple[Dict, Dict]:
    """
    Fetch capabilities and basic capabilities from the Observatory State Database (OSD).

    :param telescope: str, the telescope identifier (e.g., 'mid' or 'low').
    :param array_assembly: str, the specific capabilities (e.g., 'AAO.5', 'AA0.1').
    :param tm_data: Optional[Dict], the telemodel data object.
    :param osd_data: Optional[Dict], the OSD data dictionary passed externally.
    :returns: A tuple containing the capabilities and basic capabilities dictionaries.
    """
    from ska_ost_osd.osd.osd import get_osd_data

    if osd_data:
        fetched_osd_data = osd_data
    else:
        fetched_osd_data, _ = get_osd_data(
            capabilities=[telescope],
            array_assembly=array_assembly,
            tmdata=tm_data,
        )

    capabilities = fetched_osd_data.get("capabilities", {}).get(telescope, {})
    if capabilities:
        return (
            capabilities.get(array_assembly, {}),
            capabilities.get("basic_capabilities", {}),
        )

    return {}, {}


def search_nested_dict(data: list | dict, key_to_find: str) -> dict | None:
    """
    Efficiently search a nested dictionary and list structure to find the value
    for the given key.

    Args:
        data (dict or list): The nested data structure to search.
        key_to_find (str): The key to search for.

    Returns:
        The value associated with the given key, or None if the key is not found.
    """
    if data is None:
        return None

    stack = [(data, [])]
    while stack:
        current, path = stack.pop()
        if isinstance(current, dict):
            if key_to_find in current.values():
                return current
            for key, value in current.items():
                if isinstance(value, (dict, list)):
                    stack.append((value, path + [key]))
        elif isinstance(current, list):
            for item in reversed(current):
                if isinstance(item, (dict, list)):
                    stack.append((item, path))
    return None


def replace_nested_value(nested_dict: Dict, path: List[str], new_value: Any) -> None:
    """
    Replace the value of a nested key in a dictionary.

    :param nested_dict: Dict, the dictionary to modify.
    :param path: List[str], the path to the key to replace, represented as a list of keys.
    :param new_value: Any, the new value to assign to the key.
    :raises KeyError: If any key in the path is not found in the nested dictionary.
    :raises TypeError: If the path does not lead to a dictionary.
    """
    current = nested_dict
    for key in path[:-1]:
        if not isinstance(current, dict) or key not in current:
            raise KeyError(f"Key '{key}' not found in the nested dictionary.")
        current = current[key]

    if not isinstance(current, dict):
        raise TypeError("The path does not lead to a dictionary.")

    last_key = path[-1]
    if last_key not in current:
        raise KeyError(f"Key '{last_key}' not found in the nested dictionary.")

    current[last_key] = new_value


def fetch_matched_capabilities_from_basic_capabilities(
    capabilities: dict, basic_capabilities: dict
) -> list:
    """
    This methods returns matched capabilities data list based
    on basic capabilities.
    e.g after fetching capabilities and basic_capabilities from OSD needs
    to rearrange some data between basic capabilities and capabilities
    so that we can easily search rule value.
    here Band_1 (min and max) frequency present in basic capabilities so
    value fetched according.
    capabilities = {
                "available_receivers": ["Band_1"]
            }
    basic_capabilities = {
                "dish_elevation_limit_deg": 15.0,
                "receiver_information": [
                    {
                        "rx_id": "Band_1",
                        "min_frequency_hz": 350000000.0,
                        "max_frequency_hz": 1050000000.0,
                    }]
                }
    matched 'rx_id:Band_1' from basic capabilities below is output dict
    matched_capabilities_list = [
            {
                "Band_1":
                    {
                        "min_frequency_hz": 350000000.0,
                        "max_frequency_hz": 1050000000.0,
                    }
            }
        ]
    : param capabilities: dict contains capabilities
        like AAO.5, AA0.1
    : param basic_capabilities: dict dict contains basic
        capabilities required for capabilities.
    : param matched_capabilities_list: replaceable data list
    : return: matched value from basic capabilities
    """
    clone_capabilities = capabilities.copy()
    stack = [(capabilities, [])]
    replacible_values = []
    while stack:
        current, path = stack.pop()
        if isinstance(current, dict):
            for key, value in current.items():
                if isinstance(key, (str, int)) and isinstance(value, (str, int)):
                    matched_values = search_nested_dict(basic_capabilities, key)
                    if matched_values:
                        replacible_values.append(matched_values)
                if isinstance(value, (dict, list)):
                    stack.append((value, path + [key]))

        elif isinstance(current, list):
            for item in reversed(current):
                if isinstance(item, (dict, list)):
                    stack.append((item, path))
                else:
                    # search key into basic capabilities
                    matched_values = search_nested_dict(basic_capabilities, item)
                    if matched_values:
                        replacible_values.append(matched_values)
    replace_nested_value(clone_capabilities, path, replacible_values)
    return clone_capabilities


def validate_command_input(
    observing_command_input: dict,
    tm_data: TMData,
    interface: str,
    array_assembly: str,
    osd_data: dict,
) -> list:
    """
    This method invoking semantic validation for given command input.
    :param observing_command_input: user json input for semantic validation
    :param tm_data: TMData object which created externally
    :param interface: assign/configure resource schema interface name
    :param array_assembly: specific capabilities like AA0.5, AA1
    :param osd_data: osd_data dict which passed externally
    :return list of error messages in case of validation failed
    """
    semantic_validate_data = tm_data[get_validation_data(interface)].get_dict()
    # call OSD API and fetch capabilities and basic capabilities
    capabilities, basic_capabilities = fetch_capabilities_from_osd(
        telescope=semantic_validate_data["telescope"],
        array_assembly=array_assembly,
        tm_data=tm_data,
        osd_data=osd_data,
    )
    msg_list = validate_json(
        semantic_validate_data[array_assembly],
        command_input_json_config=observing_command_input,
        parent_key=None,
        capabilities=fetch_matched_capabilities_from_basic_capabilities(
            capabilities=capabilities, basic_capabilities=basic_capabilities
        ),
    )

    return msg_list


def semantic_validate(
    observing_command_input: Dict,
    tm_data: Dict,
    array_assembly: str = "AA0.5",
    interface: Optional[str] = None,
    raise_semantic: bool = True,
    osd_data: Optional[Dict] = None,
) -> bool:
    """
    This method is the entry point for semantic validation, which can be consumed by
    other libraries like CDM.

    :param observing_command_input: dictionary containing details of the command which needs validation.
    This is the same as for ska_telmodel.schema.validate.
    If the command is available as a JSON string, first convert it to a dictionary using json.loads.
    :param tm_data: telemodel tm data object using which we can load the semantic validation JSON.
    :param osd_data: osd_data dict which is passed externally.
    :param interface: interface URI in full, only provide if missing in observing_command_input.
    :param array_assembly: Array assembly like AA0.5, AA0.1.
    :param raise_semantic: True (default) would require the user to catch the SchematicValidationError somewhere.
    Set False to only log the error messages.
    :returns: True if semantic validation passes, False otherwise.
    """
    version = observing_command_input.get("interface") or interface

    if not version:
        message = (
            "Interface is missing from observing_command_input. Please provide"
            " interface='...' explicitly."
        )
        logging.warning(message)
        raise SchematicValidationError(message)

    msg_list = validate_command_input(
        observing_command_input, tm_data, version, array_assembly, osd_data
    )
    msg_list = [msg for msg in msg_list if msg]  # Remove None values

    if msg_list:
        msg = "\n".join(msg_list)
        logging.error(
            "Also following errors were encountered during semantic"
            f" validations:\n{msg}"
        )
        if raise_semantic:
            raise SchematicValidationError(msg)
        return False

    return True
