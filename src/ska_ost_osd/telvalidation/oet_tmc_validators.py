"""
This module retrieves semantic validation constants
constant file contains specific error messages and rules,
while execution of assign resource, configure command
from jupyter notebook or any UI we are validating json
payload which provided for execution of specific command.
Rule file contains constraints and those values are fetched from
OSD capabilities.
e.g: in rule file below is rule and error messages.
"rule": "(0 < length(receptor_ids) <= number_ska_dishes)"
"error": "receptor_ids are too many!Current Limit is {number_ska_dishes}"
here 'number_ska_dishes' constraints value fetched from
OSD capabilities.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Union

import astropy.units as u
from astropy.time import Time
from simpleeval import EvalWithCompoundTypes

from .constant import MID_VALIDATION_CONSTANT_JSON_FILE_PATH
from .coordinates_conversion import (
    dec_degs_str_formats,
    ra_dec_to_az_el,
    ra_degs_from_str_formats,
)
from .schematic_validation_exceptions import (
    SchemanticValdidationKeyError,
    SchematicValidationError,
)

logging.getLogger("telvalidation")


from collections import deque


def get_value_based_on_key(nested_data: Union[Dict, List], path: List) -> Any:
    """
    Retrieve a value from a nested dictionary or
    list of dictionaries based on a given path.

    Args:
        nested_data (dict or list): The nested dictionary or
        list of dictionaries to search.
        path (list): A list of keys representing the path to the desired value.

    Returns:
        The value at the specified path, or None if the path is invalid
        or the value is not found.
    """
    stack = deque()
    stack.append((nested_data, path))

    while stack:
        current_data, remaining_path = stack.pop()

        if not remaining_path:
            return current_data

        current_key = remaining_path[0]
        remaining_path = remaining_path[1:]

        if isinstance(current_data, dict):
            if current_key in current_data:
                stack.append((current_data[current_key], remaining_path))
            else:
                # Check if the current key exists in any nested dictionary
                for value in current_data.values():
                    if isinstance(value, dict):
                        stack.append((value, [current_key] + remaining_path))
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                stack.append((item, [current_key] + remaining_path))
        elif isinstance(current_data, list):
            for item in current_data:
                if isinstance(item, dict) and current_key in item:
                    value = item[current_key]
                    if not remaining_path:
                        return value
                    elif isinstance(remaining_path[0], int):
                        # Handle case where the next key is an integer (list index)
                        next_key = remaining_path[0]
                        remaining_path = remaining_path[1:]
                        if isinstance(value, list) and next_key < len(value):
                            stack.append((value, [next_key] + remaining_path))
                    else:
                        stack.append((value, remaining_path))
        else:
            return None

    return None


def get_matched_rule_constraint_from_osd(
    basic_capabilities: dict, search_key: str, rule: str
) -> list:
    """
    This function returns a list of matched key-value dictionaries
    based on the rule value.

    Example:
    The updated structure of basic capabilities and rule is below:
    capabilities = {
        "available_receivers": [{
            "rx_id": "Band_1",
            "min_frequency_hz": 350000000.0,
            "max_frequency_hz": 1050000000.0,
        }],
        "number_ska_dishes": 4
    }

    Rule from mid-validation-constant.json:
    "freq_min": [
        {
            "rule": "min_frequency_hz <= freq_min <= max_frequency_hz",
            "error": "Invalid input for freq_min"
        }
    ]

    min_frequency_hz and max_frequency_hz rule constraints
    are matched from
    capabilities, hence the output list becomes
    [{"min_frequency_hz": 350000000.0,
    "max_frequency_hz": 1050000000.0}]

    :param basic_capabilities: Capabilities from OSD
    :param search_key: Keys from the rule file
    :return: A list of matched capabilities based on the rule file keys
    """
    result = []
    stack = [basic_capabilities]

    while stack:
        current_dict = stack.pop()

        if isinstance(current_dict, dict):
            temp_value = {}
            for key, value in current_dict.items():
                if rule and key in rule:
                    temp_value.update({key: value})
                if isinstance(value, dict):
                    stack.append(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            stack.append(item)
                if key == search_key or value == search_key:
                    result.append(current_dict)
            if temp_value:
                result.append(temp_value)

    return result


def apply_validation_rule(
    key: str,
    value: List[Dict[str, Union[str, Dict]]],
    command_input_json_config: Dict,
    parent_key: str,
    capabilities: Dict,
) -> str:
    """
    Evaluate validation rules using simpleeval and
    return an error message if the input is invalid.

    :param key: str, the user input key for search.
    :param value: List[Dict[str, Union[str, Dict]]],
    a list of dictionaries containing the rule and error.
    :param command_input_json_config: Dict,
    the command input JSON from the operator.
    :param parent_key: str, the parent key to
    identify the correct child key.
    :param capabilities: Dict, the capabilities dictionary.
    :return: str, the error message after applying the rule.
    """
    res_value = get_value_based_on_key(command_input_json_config, [parent_key, key])
    if res_value:
        add_semantic_variables({key: res_value})
        error_msgs = []

        for rule_data in value:
            try:
                osd_base_constraint = get_matched_rule_constraint_from_osd(
                    basic_capabilities=capabilities,
                    search_key=None,
                    rule=rule_data["rule"],
                )
                eval_result = evaluate_rule(
                    key,
                    res_value,
                    rule_data,
                    osd_base_constraint,
                )
                if eval_result and True not in eval_result:
                    error_msg = format_error_message(rule_data, osd_base_constraint)
                    error_msgs.append(error_msg)
            except KeyError as key_error:
                logging.error(key_error)
                raise SchemanticValdidationKeyError(  # pylint: disable=W0707
                    message="Invalid rule and error key passed"
                )

        return "\n".join(error_msgs)

    return ""


def evaluate_rule(
    key: str,
    res_value: Union[str, List],
    rule_data: Dict[str, Union[str, Dict]],
    osd_base_constraint: List[Dict],
) -> bool:
    """
    Evaluate a single validation rule using simpleeval.

    :param key: str, the user input key for search.
    :param res_value: Union[str, List], the value of the key.
    :param rule_data: Dict[str, Union[str, Dict]], the rule and error data.
    :param osd_base_constraint: List[Dict], the list of dictionaries
    containing the rule keys.
    :param eval_functions: Dict, the dictionary of functions for simpleeval.
    :return: bool, True if the rule is satisfied, False otherwise.
    """
    names = {}
    eval_new_data = []
    simple_eval = EvalWithCompoundTypes()
    simple_eval.functions["len"] = len
    if len(osd_base_constraint) > 1:
        for i in osd_base_constraint:
            names = {key: res_value}
            names = {**names, **i}
            simple_eval.names = names
            eval_data = simple_eval.eval(rule_data["rule"])
            if eval_data is False or (
                not isinstance(eval_data, bool) and len(eval_data) > 0
            ):
                eval_new_data.append(False)
            else:
                eval_new_data.append(True)
    else:
        if osd_base_constraint:
            osd_base_constraint_value = osd_base_constraint[0]
        else:
            osd_base_constraint_value = {}

        if "dependency_key" in rule_data:
            dependency_values = get_semantic_variables()
            names = {
                key: res_value,
                rule_data["dependency_key"]: dependency_values[
                    rule_data["dependency_key"]
                ],
            }
        else:
            names = {key: res_value}
            names = {**names, **osd_base_constraint_value}

        simple_eval.names = names
        eval_data = simple_eval.eval(rule_data["rule"])

        if isinstance(eval_data, set) and len(eval_data) == 0:
            eval_new_data.append(True)
        if isinstance(eval_data, set) and len(eval_data) > 0:
            eval_new_data.append(False)
        else:
            eval_new_data.append(bool(eval_data))

    return eval_new_data


def format_error_message(
    rule_data: Dict[str, Union[str, Dict]], rule_key_dict: List[Dict]
) -> str:
    """
    Format the error message for a failed validation rule.

    :param rule_data: Dict[str, Union[str, Dict]], the rule and error data.
    :param rule_key_dict: List[Dict], the list of dictionaries containing the rule keys.
    :return: str, the formatted error message.
    """
    if rule_key_dict:
        rule_key_dict_new = rule_key_dict[0]
        return rule_data["error"].format(**rule_key_dict_new)
    return rule_data["error"]


def validate_json(
    semantic_validate_constant_json: dict,
    command_input_json_config: dict,
    parent_key: str,
    capabilities: dict,
) -> list:
    """
    This function is written to matching key's from user input command
    and validation constant rules those and present in mid, low
    and SBD validation constant json.
    e.g consider one of the assign resource command dish rule
    from constant json.
    here we are just mapping rule dish of receptor_ids to
    user assign resource command input payload.
    :param semantic_validate_constant_json: json containing all the parameters
    along with its business semantic validation rules and error message.
    :param command_input_json_config: dictionary containing
    details of the command input which needs validation.
    This is same as for ska_telmodel.schema.validate.
    :param parent_key: temp key to store parent key, means if same semantic
    validation key present in 2 places this will help to identify
    correct parent.
    :param capabilities: defined key, value structure pair from OSD API
    :returns: error_msg_list: list containing all combined error which arises
    due to semantic validation.
    """
    # initially declared empty values for error messages list, last parent dict
    # and parent key
    error_msg_list = []
    for key, value in semantic_validate_constant_json.items():
        if isinstance(value, list):
            # if validation key present in multiple dict parent_key
            # helps to populate current child
            rule_result = apply_validation_rule(
                key=key,
                value=value,
                command_input_json_config=command_input_json_config,
                parent_key=parent_key,
                capabilities=capabilities,
            )
            if rule_result:
                error_msg_list.append(rule_result)

        elif isinstance(value, dict):
            # added extra key as rule parent to perform rule validation
            # on child
            # e.g semantic rule suggest calculate beams length but beams
            # is having array of element, in this case parent_rule_key
            # key helps to apply rule on child]
            if "parent_key_rule" in value:
                rule_key = list(value.keys())[1]
                rule_result = apply_validation_rule(
                    key=rule_key,
                    value=value["parent_key_rule"],
                    command_input_json_config=command_input_json_config,
                    parent_key=key,
                    capabilities=capabilities,
                )
                if rule_result:
                    error_msg_list.append(rule_result)
            parent_key = key
            error_msg_list.extend(
                validate_json(
                    value,
                    command_input_json_config,
                    parent_key,
                    capabilities,
                )
            )
    return error_msg_list


def validate_target_is_visible(
    ra_str: str,
    dec_str: str,
    telescope: str,
    target_env: str,
    tm_data,
    observing_time: datetime = datetime.utcnow(),
) -> str:
    """
    Check the target specific by ra,dec is visible
    during observing_time at telescope site

    :param ra_str: string containing value of ra
    :param dec_str: string containing value of dec
    :param telescope: string containing name of the telescope
    :param observing_time: string containing value of observing_time
    :param target_env: string containing the environment value(mid/low)
            for the target
    :param tm_data: telemodel tm dataobject using which
            we can load semantic validate json.
    """
    observing_time = observing_time.strftime("%Y-%m-%dT%H:%M:%S")
    utcoffset = +2 * u.hour if target_env == "target_mid" else +8 * u.hour
    observing_time = (Time(observing_time) - utcoffset).strftime("%Y-%m-%dT%H:%M:%S")
    validator_json_schema = tm_data[MID_VALIDATION_CONSTANT_JSON_FILE_PATH].get_dict()
    dish_elevation_limit = validator_json_schema["AA0.5"]["dish_elevation_limit"]["min"]

    ra_dec = [
        ra_degs_from_str_formats(ra_str)[0],
        dec_degs_str_formats(dec_str)[0],
    ]
    temp_list = ra_dec_to_az_el(
        telesc=telescope,
        ra=ra_dec[0],
        dec=ra_dec[1],
        obs_time=observing_time,
        el_limit=dish_elevation_limit,
        if_set=True,
        time_format="isot",
        tm_data=tm_data,
    )

    if len(temp_list) >= 3 and temp_list[2]:
        return True
    else:
        error_message = (
            f"Telescope: {telescope} target observing during {observing_time} "
            "is not visible"
        )
        logging.error(error_message)
        raise SchematicValidationError(error_message)


_semantic_validate_data = {}


def add_semantic_variables(semantic_object: Any):
    _semantic_validate_data.update(semantic_object)


def get_semantic_variables():
    return _semantic_validate_data


def clear_semantic_variable_data():
    _semantic_validate_data.clear()
