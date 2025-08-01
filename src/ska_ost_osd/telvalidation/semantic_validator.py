"""This module contains the 'semantic_validate' functions which is exposed to
outside for use.

If observing command's input contains invalid values it will raise
validation error's based on provided rules. Integrated OSD API function
to fetch rule constraints values.
"""

import logging
from os import environ
from typing import Any, Optional

from pydantic import ValidationError
from ska_telmodel.data import TMData

from ska_ost_osd.telvalidation.models.semantic_schema_validator import SemanticModel

from .common.constant import (
    ASSIGN_RESOURCE,
    CONFIGURE,
    LOW_SBD_VALIDATION_CONSTANT_JSON_FILE_PATH,
    LOW_VALIDATION_CONSTANT_JSON_FILE_PATH,
    MID_SBD_VALIDATION_CONSTANT_JSON_FILE_PATH,
    MID_VALIDATION_CONSTANT_JSON_FILE_PATH,
    SEMANTIC_VALIDATION_VALUE,
    SKA_LOW_SBD,
    SKA_LOW_TELESCOPE,
    SKA_MID_SBD,
    SKA_MID_TELESCOPE,
)
from .common.error_handling import SchematicValidationError
from .oet_tmc_validators import clear_semantic_variable_data, validate_json

logging.getLogger("telvalidation")

VALIDATION_STRICTNESS = environ.get("VALIDATION_STRICTNESS", "2")


def get_validation_data(interface: str, telescope: str) -> Optional[str]:
    """Get the validation constant JSON file path based on the provided
    interface URI.

    :param interface: str, the interface URI from the observing command
        input.
    :param telescope: str, the telescope identifier (e.g., 'mid' or
        'low').
    :return: str, the validation constant JSON file path, or None if not
        found.
    """
    validation_constants = {
        SKA_LOW_TELESCOPE: LOW_VALIDATION_CONSTANT_JSON_FILE_PATH,
        SKA_MID_TELESCOPE: MID_VALIDATION_CONSTANT_JSON_FILE_PATH,
        SKA_MID_SBD: MID_SBD_VALIDATION_CONSTANT_JSON_FILE_PATH,
        SKA_LOW_SBD: LOW_SBD_VALIDATION_CONSTANT_JSON_FILE_PATH,
    }

    for key, value in validation_constants.items():
        if key in interface or key == telescope:
            return value

    # taking mid interface as default cause there is no any specific
    # key to differentiate the interface
    return validation_constants.get(SKA_MID_TELESCOPE)


def fetch_capabilities_from_osd(
    telescope: str,
    array_assembly: str,
    tm_data: Optional[dict] = None,
    osd_data: Optional[dict] = None,
) -> tuple[dict, dict]:
    """Fetch capabilities and basic capabilities from the Observatory State
    Database (OSD).

    :param telescope: str, the telescope identifier (e.g., 'mid' or
        'low').
    :param array_assembly: str, the specific capabilities (e.g.,
        'AAO.5', 'AA0.1').
    :param tm_data: Optional[Dict], the telemodel data object.
    :param osd_data: Optional[Dict], the OSD data dictionary passed
        externally.
    :returns: A tuple containing the capabilities and basic capabilities
        dictionaries.
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


def get_matched_values_from_basic_capabilities(
    data: list | dict, key_to_find: str
) -> dict | None:
    """Efficiently search a nested dictionary and list structure to find the
    value for the given key from basic capabilities.

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


def replace_matched_capabilities_values(
    nested_dict: dict, path: list[str], new_value: Any
) -> None:
    """Replace the value in capabilities data which matched from basic
    capabilities.

    :param nested_dict: Dict, the dictionary to modify.
    :param path: List[str], the path to the key to replace, represented
        as a list of keys.
    :param new_value: Any, the new value to assign to the key.
    :raises KeyError: If any key in the path is not found in the nested
        dictionary.
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


def build_reference_lookups(source_data):
    ref_lookups = {}

    def collect(node):
        if isinstance(node, dict):
            for _, v in node.items():
                if isinstance(v, list) and all(isinstance(i, dict) for i in v):
                    for item in v:
                        for ik, _ in item.items():
                            if ik.endswith("_id"):
                                ref_lookups.setdefault(ik, {})[item[ik]] = item
                else:
                    collect(v)
        elif isinstance(node, list):
            for item in node:
                collect(item)

    collect(source_data)
    return ref_lookups


def recursive_replace_references(target, lookups):
    if isinstance(target, dict):
        return {k: recursive_replace_references(v, lookups) for k, v in target.items()}
    elif isinstance(target, list):
        if all(isinstance(i, str) for i in target):
            for _, mapping in lookups.items():
                if all(val in mapping for val in target):
                    return [mapping[val] for val in target]
        return [recursive_replace_references(i, lookups) for i in target]
    return target


def validate_command_input(
    observing_command_input: dict,
    tm_data: TMData,
    interface: str,
    telescope: str,
    array_assembly: str,
    osd_data: dict,
) -> list:
    """This method invoking semantic validation for given command input.

    :param observing_command_input: user json input for semantic
        validation
    :param tm_data: TMData object which created externally
    :param interface: assign/configure resource schema interface name
    :param telescope: str, the telescope identifier (e.g., 'mid' or
        'low').
    :param array_assembly: specific capabilities like AA0.5, AA1
    :param osd_data: osd_data dict which passed externally :return list
        of error messages in case of validation failed
    """
    semantic_validate_data = tm_data[
        get_validation_data(interface, telescope)
    ].get_dict()
    # call OSD API and fetch capabilities and basic capabilities
    capabilities, basic_capabilities = fetch_capabilities_from_osd(
        telescope=semantic_validate_data["telescope"],
        array_assembly=array_assembly,
        tm_data=tm_data,
        osd_data=osd_data,
    )
    lookup_table = build_reference_lookups(basic_capabilities)
    matched_capabilities = recursive_replace_references(capabilities, lookup_table)
    validation_data = semantic_validate_data[array_assembly].get(
        "assign_resource"
        if ASSIGN_RESOURCE in interface
        else "configure"
        if CONFIGURE in interface
        else "sbd"
    )

    msg_list = validate_json(
        validation_data,
        command_input_json_config=observing_command_input,
        parent_path_list=[],
        capabilities=matched_capabilities,
    )

    return msg_list


def semantic_validate(
    observing_command_input: dict,
    tm_data: TMData,
    array_assembly: str = "AA0.5",
    interface: Optional[str] = None,
    raise_semantic: bool = True,
    osd_data: Optional[dict] = None,
) -> Any:
    """This method is the entry point for semantic validation, which can be
    consumed by other libraries like CDM.

    :param observing_command_input: dictionary containing details of the
        command which needs validation.This is the same as for
        ska_telmodel.schema.validate. If the command is available as a
        JSON string, first convert it to a dictionary using json.loads.
    :param tm_data: telemodel tm data object using which we can load the
        semantic validation JSON.
    :param osd_data: osd_data dict which is passed externally.
    :param interface: interface URI in full, only provide if missing in
        observing_command_input.
    :param array_assembly: Array assembly like AA0.5, AA0.1.
    :param raise_semantic: True (default) would require the user to
        catch the SchematicValidationError somewhere. Set False to only
        log the error messages.
    :returns: True if semantic validation passes, False otherwise.
    """
    if int(VALIDATION_STRICTNESS) == SEMANTIC_VALIDATION_VALUE:
        try:
            SemanticModel(
                observing_command_input=observing_command_input,
                tm_data=tm_data,
                array_assembly=array_assembly,
                interface=interface,
                raise_semantic=raise_semantic,
                osd_data=osd_data,
            )
        except ValidationError as err:
            raise err
        except ValueError as semantic_error:
            raise semantic_error
        clear_semantic_variable_data()
        version = observing_command_input.get("interface") or interface
        telescope = observing_command_input.get("telescope")

        if not version:
            message = (
                "Interface is missing from observing_command_input. Please provide"
                " interface='...' explicitly."
            )
            logging.warning(message)
            raise SchematicValidationError(message)

        msg_list = validate_command_input(
            observing_command_input,
            tm_data,
            version,
            telescope,
            array_assembly,
            osd_data,
        )
        msg_list = [msg for msg in msg_list if msg]  # Remove None values

        if msg_list:
            msg = "\n".join(msg_list)
            logging.error(
                "Also following errors were encountered during semantic %s",
                f"validations:\n{msg}",
            )
            if raise_semantic:
                raise SchematicValidationError(msg)
            return False

    return True
