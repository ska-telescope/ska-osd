"""
This module contains the 'semantic_validate' functions which is exposed
to outside for use. If observing command's input contains invalid
values it will raise validation error's based on provided rules.
Integrated OSD API function to fetch rule constraints values.
"""


import copy
import logging

from ska_telmodel.data import TMData

from .constant import (
    LOW_VALIDATION_CONSTANT_JSON_FILE_PATH,
    MID_VALIDATION_CONSTANT_JSON_FILE_PATH,
    SBD_VALIDATION_CONSTANT_JSON_FILE_PATH,
    SKA_LOW_TELESCOPE,
    SKA_MID_TELESCOPE,
    SKA_SBD,
)
from .oet_tmc_validators import (
    search_and_return_value_from_basic_capabilities,
    validate_json,
)
from .schematic_validation_exceptions import SchematicValidationError

logging.getLogger("telvalidation")


def get_validation_data(interface: str):
    """
    :param interface: interface uri from the observing_command_input.
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
    return MID_VALIDATION_CONSTANT_JSON_FILE_PATH


def fetch_capabilities_from_osd(
    telescope: str,
    array_assembly: str,
    tm_data: TMData = None,
    osd_data: dict = None,
) -> dict:
    """
    method to fetch capabilities and basic capabilities from OSD
    OSD is data storage for Observatory constant.
    :param telescope: str defined telescope mid or low
    :specific capabilities: str specific capabilities contains AAO.5, AA0.1
    :param osd_data: osd_data dict which passed externally.
    :returns: str capabilities and basic capabilities.
    """
    osd_capabilities = {}
    fetched_osd_data = {}
    if osd_data:
        fetched_osd_data = osd_data
    else:
        from ska_ost_osd.osd.osd import get_osd_data

        fetched_osd_data, _ = get_osd_data(
            capabilities=[telescope],
            array_assembly=array_assembly,
            tmdata=tm_data,
        )
    if fetched_osd_data and telescope in fetched_osd_data["capabilities"]:
        osd_capabilities = fetched_osd_data["capabilities"][telescope]
        return (
            osd_capabilities[array_assembly],
            osd_capabilities["basic_capabilities"],
        )
    return {}, {}


def search_nested_dict(data, key_to_find):
    """
    Efficiently search a nested dictionary and list structure to find the value
    for the given key.

    Args:
        data (dict or list): The nested data structure to search.
        key_to_find (str): The key to search for.

    Returns:
        The value associated with the given key, or None if the key is not found.
    """
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


def search_matched_key_data_from_basic_capabilities(
    basic_capabilities: dict, search_key: str
) -> dict:
    """
    This method is returns matched data from basic capabilities based on
    search key.
    e.g "basic_capabilities": {
                "receiver_information": [
                    {
                        "rx_id": "Band_1",
                        "min_frequency_hz": 350000000.0,
                        "max_frequency_hz": 1050000000.0,
                    }]
                }
    consider 'Band_1' is search key once it matched result
    contains entire dict.
    {
        "rx_id": "Band_1",
        "min_frequency_hz": 350000000.0,
        "max_frequency_hz": 1050000000.0,
    }
    : param basic_capabilities: dict basic capabilities from OSD
    : param search_key: key needs to be searched
    : return: entire dict or list around matched keys
    """
    search_result = search_and_return_value_from_basic_capabilities(
        basic_capabilities=basic_capabilities,
        search_key=search_key,
        rule=None,
        result=[],
    )
    return search_result


def replace_values_after_matched_from_basic_capabilities(
    matched_capabilities: dict, capabilities: dict
) -> dict:
    """
    This method return new capabilities dict after replaced
    from basic_capabilities
    refer capabilities dict from test_semantic_validator.py
    before replacement of available_receivers
    "AA0.5": {
                "available_receivers": ["Band_1", "Band_2"]
            }
    after replaced available_receiver value from basic capabilities
    "AA0.5": {
                "available_receivers": [{
                        "rx_id": "Band_1",
                        "min_frequency_hz": 350000000.0,
                        "max_frequency_hz": 1050000000.0,
                    },
                    {
                        "rx_id": "Band_2",
                        "min_frequency_hz": 950000000.0,
                        "max_frequency_hz": 1760000000.0,
                    }]
            }

    : param matched_capabilities: matched capabilities from basic capabilities
    : param: original capabilities needs to be replaced
    """
    for key, value in capabilities.items():
        if isinstance(value, list):
            temp_list = []
            for data in value:
                mapped_values = [
                    value[data] for value in matched_capabilities if data in value
                ]
                if mapped_values:
                    temp_list.append(mapped_values[0])
            if temp_list:
                capabilities[key] = temp_list
    return capabilities


# refer search_nested_dictmethod and restructure below code


def fetch_matched_capabilities_from_basic_capabilities(
    capabilities: dict,
    basic_capabilities: dict,
    matched_capabilities_list: list,
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

    stack = [(capabilities, [])]
    while stack:
        current, path = stack.pop()
        if isinstance(current, dict):
            for key, value in current.items():
                if isinstance(key, (str, int)) and isinstance(value, (str, int)):
                    matched_values = search_nested_dict(basic_capabilities, key)
                    if matched_values:
                        matched_capabilities_list.append({key: matched_values})
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
                        matched_capabilities_list.append({item: matched_values})
    return matched_capabilities_list


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
    copied_capabilities = copy.deepcopy(capabilities)
    # after fetching data from OSD storage matching and replacing json values
    # for further use cases
    matched_capabilities = fetch_matched_capabilities_from_basic_capabilities(
        capabilities=capabilities,
        basic_capabilities=basic_capabilities,
        matched_capabilities_list=[],
    )
    osd_capabilities = replace_values_after_matched_from_basic_capabilities(
        matched_capabilities, copied_capabilities
    )

    msg_list = validate_json(
        semantic_validate_data[array_assembly],
        command_input_json_config=observing_command_input,
        error_msg_list=[],
        parent_key=None,
        capabilities=osd_capabilities,
    )

    return msg_list


def semantic_validate(
    observing_command_input: dict,
    tm_data: TMData,
    array_assembly: str = "AA0.5",
    interface: str = None,
    raise_semantic: bool = True,
    osd_data: dict = None,
) -> any:
    """
    This method is entry point for semantic validation which can be consumed by
    other libraries like CDM.
    :param observing_command_input: dictionary containing details
    of the command which needs validation.
    This is same as for ska_telmodel.schema.validate.
    If command available as json string
    first convert to dictionary by json.loads.
    :param tm_data: telemodel tm data object using which
    we can load semantic validate json.
    :param osd_data: osd_data dict which passed externally
    :param interface: interface uri in full only provide if
    missing in observing_command_input
    :param array_assembly: Array assembly like AA0.5, AA0.1
    :param raise_semantic: True(default) would need user
    to catch somewhere the SchematicValidationError.
    Set False to only log the error messages.
    :returns: msg: if semantic validation fail returns error message containing
    all combined error which arises else returns True.
    """
    # fetching interface value from observing_command_input
    version = observing_command_input.get("interface")
    if version is None:
        version = interface
    # if still version remain null
    if version is None:
        message = """interface is missing from observing_command_input.
        Please provide interface='...' explicitly"""
        logging.warning(message)
        raise SchematicValidationError(message)
    msg = ""
    msg_list = validate_command_input(
        observing_command_input, tm_data, version, array_assembly, osd_data
    )
    msg_list = [k for k in msg_list if k is not None]
    msg = "\n".join(msg_list) if msg_list else msg
    # add in the list the specific substrings
    # which when appear in message indicate no error
    # success_keys=["Success!","Is visible?Yes","1","2"]
    if msg is not None and msg != "":
        # pylint: disable=logging-not-lazy
        logging.error(
            """Also following errors were encountered
              during semantic validations:\n"""
            + msg
        )
        if raise_semantic is True:
            raise SchematicValidationError(msg)
    return True
