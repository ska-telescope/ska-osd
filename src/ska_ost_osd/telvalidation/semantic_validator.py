"""This module contains the 'semantic_validate' functions which is exposed to
outside for use.

If observing command's input contains invalid values it will raise
validation error's based on provided rules. Integrated OSD API function
to fetch rule constraints values.
"""

import logging
from os import environ
from typing import Any, Dict, Optional

from pydantic import ValidationError
from ska_telmodel.data import TMData

from ska_ost_osd.telvalidation.models.semantic_schema_validator import (
    SemanticModel,
)

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
    :return: Optional[str], the validation constant JSON file path, or
        None if not found.
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
    :return: Tuple[Dict, Dict], a tuple containing the capabilities and
        basic capabilities dictionaries.
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

    :param data: dict or list, the nested data structure to search.
    :param key_to_find: str, the key to search for.
    :return: The value associated with the given key, or None if the key
        is not found.
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
    """Replace the value in capabilities data that matches a key from basic
    capabilities.

    :param nested_dict: dict, the dictionary to modify.
    :param path: list[str], the path to the key to replace, represented
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


def build_basic_capabilities_lookup(
    basic_capabilities: Any,
) -> Dict[str, Dict[str, Any]]:
    """Builds reference lookup dictionary from nested basic capabilities data.

    :param basic_capabilities: nested capability data containing lists
        of items with '_id' fields :return dictionary mapping each
        reference type to its corresponding item by id
    :example:
        >>> basic_capabilities = {
        ...     'dish_elevation_limit_deg': 15,
        ...     'receiver_information': [
        ...         {'max_frequency_hz': 1050000000, 'min_frequency_hz': 350000000,
        'rx_id': 'Band_1'},
        ...         {'max_frequency_hz': 1760000000, 'min_frequency_hz': 950000000,
        'rx_id': 'Band_2'},
        ...         {'max_frequency_hz': 3050000000, 'min_frequency_hz': 1650000000,
        'rx_id': 'Band_3'}
        ...     ]
        ... }
        >>> build_basic_capabilities_lookup(basic_capabilities)
        {
            'rx_id': {
                'Band_1': {'max_frequency_hz': 1050000000,
                'min_frequency_hz': 350000000, 'rx_id': 'Band_1'},
                'Band_2': {'max_frequency_hz': 1760000000,
                'min_frequency_hz': 950000000, 'rx_id': 'Band_2'},
                'Band_3': {'max_frequency_hz': 3050000000,
                'min_frequency_hz': 1650000000, 'rx_id': 'Band_3'}
            }
        }
    """

    capabilities_lookup: Dict[str, Dict[str, Any]] = {}

    def collect(node: Any) -> None:
        if isinstance(node, dict):
            for value in node.values():
                if isinstance(value, list) and all(
                    isinstance(item, dict) for item in value
                ):
                    for item in value:
                        for key in item:
                            if key.endswith("_id"):
                                capabilities_lookup.setdefault(key, {})[
                                    item[key]
                                ] = item
                else:
                    collect(value)
        elif isinstance(node, list):
            for item in node:
                collect(item)

    collect(basic_capabilities)
    return capabilities_lookup


def fetch_matched_capabilities_from_basic_capabilities(
    capabilities: Any, basic_capabilities: Dict[str, Dict[str, Any]]
) -> Any:
    """Recursively matches and replaces capability references using basic
    capability mappings.

    :param capabilities: input capabilities data as nested dict, list,
        or scalar
    :param basic_capabilities: lookup dictionary mapping reference keys
        to capability details :return transformed capabilities with
        matched basic capability values

    :example:
        >>> capabilities = {
        ...     'allowed_channel_count_range_max': [58982],
        ...     'allowed_channel_count_range_min': [1],
        ...     'allowed_channel_width_values': [13440],
        ...     'available_bandwidth_hz': 800000000,
        ...     'available_receivers': ['Band_1', 'Band_2'],
        ...     'cbf_modes': ['correlation', 'pst'],
        ...     'max_baseline_km': 1.5,
        ...     'number_dish_ids': ['SKA001', 'SKA036', 'SKA063', 'SKA100'],
        ...     'number_fsps': 4,
        ...     'number_meerkat_dishes': 0,
        ...     'number_meerkatplus_dishes': 0,
        ...     'number_pss_beams': 0,
        ...     'number_pst_beams': 1,
        ...     'number_ska_dishes': 4,
        ...     'number_zoom_channels': 0,
        ...     'number_zoom_windows': 0,
        ...     'ps_beam_bandwidth_hz': 400000000
        ... }
        >>> basic_capabilities = {
        ...     'rx_id': {
        ...         'Band_1': {'max_frequency_hz': 1050000000,
        'min_frequency_hz': 350000000,
        'rx_id': 'Band_1'},
        ...         'Band_2': {'max_frequency_hz': 1760000000,
        'min_frequency_hz': 950000000,
        'rx_id': 'Band_2'}
        ...     }
        ... }
        >>> fetch_matched_capabilities_from_basic_capabilities(capabilities,
        basic_capabilities)
        {
            'allowed_channel_count_range_max': [58982],
            'allowed_channel_count_range_min': [1],
            'allowed_channel_width_values': [13440],
            'available_bandwidth_hz': 800000000,
            'available_receivers': [
                {'max_frequency_hz': 1050000000, 'min_frequency_hz': 350000000,
                'rx_id': 'Band_1'},
                {'max_frequency_hz': 1760000000, 'min_frequency_hz': 950000000,
                'rx_id': 'Band_2'}
            ],
            'cbf_modes': ['correlation', 'pst'],
            'max_baseline_km': 1.5,
            'number_dish_ids': ['SKA001', 'SKA036', 'SKA063', 'SKA100'],
            'number_fsps': 4,
            'number_meerkat_dishes': 0,
            'number_meerkatplus_dishes': 0,
            'number_pss_beams': 0,
            'number_pst_beams': 1,
            'number_ska_dishes': 4,
            'number_zoom_channels': 0,
            'number_zoom_windows': 0,
            'ps_beam_bandwidth_hz': 400000000
        }
    """

    if isinstance(capabilities, dict):
        return {
            key: fetch_matched_capabilities_from_basic_capabilities(
                value, basic_capabilities
            )
            for key, value in capabilities.items()
        }
    elif isinstance(capabilities, list):
        if all(isinstance(item, str) for item in capabilities):
            for mapping in basic_capabilities.values():
                if all(ref in mapping for ref in capabilities):
                    return [mapping[ref] for ref in capabilities]
        return [
            fetch_matched_capabilities_from_basic_capabilities(
                item, basic_capabilities
            )
            for item in capabilities
        ]

    return capabilities


def validate_command_input(
    observing_command_input: dict,
    tm_data: TMData,
    interface: str,
    telescope: str,
    array_assembly: str,
    osd_data: dict,
) -> list:
    """Invoke semantic validation for the given command input.

    :param observing_command_input: dict, user JSON input for semantic
        validation.
    :param tm_data: TMData, the TMData object created externally.
    :param interface: str, assign/configure resource schema interface name.
    :param telescope: str, the telescope identifier (e.g., 'mid' or 'low').
    :param array_assembly: str, specific capabilities like 'AA0.5', 'AA1'.
    :param osd_data: dict, externally passed OSD data dictionary.
    :return: list, error messages if validation fails; empty list
    otherwise.
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
    capabilities_lookup = build_basic_capabilities_lookup(basic_capabilities)
    matched_capabilities = fetch_matched_capabilities_from_basic_capabilities(
        capabilities, capabilities_lookup
    )
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
    """Entry point for semantic validation, usable by other libraries like CDM.

    :param observing_command_input: dict, details of the command to validate.
     This should match the structure expected by `ska_telmodel.schema.validate`.
     If the command is a JSON string, convert it to a dictionary with
     `json.loads` first.
    :param tm_data: TMData, telemodel data object used to load semantic validation JSON.
    :param osd_data: Optional[dict], externally passed OSD data dictionary.
    :param interface: Optional[str], full interface URI; provide only if missing
     in `observing_command_input`.
    :param array_assembly: str, array assembly version like 'AA0.5' or 'AA0.1'.
    :param raise_semantic: bool, default True. If True,
     raises `SchematicValidationError` on validation failure;
     if False, only logs errors and returns False.
    :return: bool, True if semantic validation passes, False otherwise.
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
                "Interface is missing from observing_command_input. Please"
                " provide interface='...' explicitly."
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
