"""
This module retrieves semantic validation constants
constant file contains specific error messages and rules,
while execution of assign resource, configure command
from jupyter notebook or any UI we are validating json
payload which provided for execution of specific command.
Rule file contains constraints and those values are fetched from
OSD capabilities.
e.g: in rule file below is rule and error messages.
"rule": "(0 < len(receptor_ids) <= number_ska_dishes)"
"error": "receptor_ids are too many!Current Limit is {number_ska_dishes}"
here 'number_ska_dishes' constraints value fetched from
OSD capabilities.
"""

import logging
import re
from datetime import datetime
from typing import Any, Union

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


def get_value_based_on_provided_path(nested_data: Union[dict, list], path: list) -> list:
    """
    Retrieve a list of keys representing the path to the desired value
    in a nested dictionary or list of dictionaries based on a given path.

    Args:
        nested_data (dict or list): The nested dictionary or
        list of dictionaries to search.
        path (list): A list of keys representing the path to the desired value.
        e.g: This help to retrieve element from dict
        based on given path like ['a', 'b', 'c']

    Returns:
        A list of keys representing the path to the desired value, or an empty
        list if the path is invalid or the value is not found.
    """
    stack = deque()
    stack.append((nested_data, path, []))

    while stack:
        current_data, remaining_path, key_path = stack.pop()

        if not remaining_path:
            return key_path

        current_key = remaining_path[0]
        remaining_path = remaining_path[1:]

        if isinstance(current_data, dict):
            if '.' in current_key:
                # Handle dot-separated keys
                keys = current_key.split('.')
                for k in keys:
                    if k in current_data:
                        key_path.append(k)
                        current_data = current_data[k]
                    else:
                        return []
                stack.append((current_data, remaining_path, key_path))
            elif current_key in current_data:
                key_path.append(current_key)
                stack.append((current_data[current_key], remaining_path, key_path))
            else:
                # Check if the current key exists in any nested dictionary
                for value in current_data.values():
                    if isinstance(value, (dict, list)):
                        stack.append((value, [current_key] + remaining_path, key_path[:]))
        elif isinstance(current_data, list):
            for item in current_data:
                if isinstance(item, dict):
                    if current_key in item:
                        value = item[current_key]
                        key_path.append(current_key)
                        if not remaining_path:
                            print("key_path", key_path)
                            return key_path
                        
                        elif isinstance(remaining_path[0], int):
                            # Handle case where the next key is an integer (list index)
                            next_key = remaining_path[0]
                            remaining_path = remaining_path[1:]
                            if isinstance(value, list) and next_key < len(value):
                                key_path.append(str(next_key))
                                stack.append((value, remaining_path, key_path))
                        else:
                            stack.append((value, remaining_path, key_path))
                    else:
                        stack.append((item, [current_key] + remaining_path, key_path[:]))
        else:
            return []

    return []

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
    value: list[dict[str, Union[str, dict]]],
    command_input_json_config: dict,
    parent_key: str,
    capabilities: dict,
) -> str:
    """
    Evaluate validation rules using simpleeval and
    return an error message if the input is invalid.

    :param key: str, the user input key for search.
    :param value: list[dict[str, Union[str, dict]]],
    a list of dictionaries containing the rule and error.
    :param command_input_json_config: dict,
    the command input JSON from the operator.
    :param parent_key: str, the parent key to
    identify the correct child key.
    :param capabilities: dict, the capabilities dictionary.
    :return: str, the error message after applying the rule.
    """
    res_value = get_value_based_on_provided_path(
        command_input_json_config, [parent_key, key]
    )
    print("res_value", res_value)
    print("parent_keyyyyyy", parent_key, key)
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
    res_value: Union[str, list],
    rule_data: dict[str, Union[str, dict]],
    osd_base_constraint: list[dict],
) -> bool:
    """
    Evaluate a single validation rule using simpleeval.

    :param key: str, the user input key for search.
    :param res_value: Union[str, list], the value of the key.
    :param rule_data: dict[str, Union[str, dict]], the rule and error data.
    :param osd_base_constraint: list[dict], the list of dictionaries
    containing the rule keys.
    :param eval_functions: dict, the dictionary of functions for simpleeval.
    :return: bool, True if the rule is satisfied, False otherwise.
    """
    names = {}
    eval_new_data = []
    simple_eval = EvalWithCompoundTypes()
    simple_eval.functions["len"] = len
    simple_eval.functions["re"] = re

    if len(osd_base_constraint) > 1:
        # if found multiple constraints values from OSD
        for i in osd_base_constraint:
            names = {key: res_value}
            names = {**names, **i}
            simple_eval.names = names
            eval_data = simple_eval.eval(rule_data["rule"])
            if not eval_data:
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
        eval_new_data = (
            [not bool(eval_data)] if isinstance(eval_data, set) else [bool(eval_data)]
        )
    return eval_new_data


def format_error_message(
    rule_data: dict[str, Union[str, dict]], rule_key_dict: list[dict]
) -> str:
    """
    Format the error message for a failed validation rule.

    :param rule_data: dict[str, Union[str, dict]], the rule and error data.
    :param rule_key_dict: list[dict], the list of dictionaries containing the rule keys.
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
        # current_key = f"{parent_key}. {key}" if parent_key else key
        
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
            print("@@@@@@@@@@@@@@@@@@@@2", rule_result)
            if rule_result:
                error_msg_list.append(rule_result)

        elif isinstance(value, dict):
            # added extra key as rule parent to perform rule validation
            # on child
            # e.g semantic rule suggest calculate beams length but beams
            # is having array of element, in this case parent_rule_key
            # key helps to apply rule on child]
            new_parent_key = f"{parent_key}.{key}" if parent_key else key
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
                    new_parent_key,
                    capabilities,
                )
            )
            
    return error_msg_list


# def validate_json(semantic_validation_constant_json, command_input_json_config, parent_keys=None, capabilities=None):
#     """
#     This function validates the user's input JSON against the semantic validation constant JSON.

#     Args:
#         semantic_validation_constant_json (dict): The semantic validation constant JSON containing the validation rules.
#         command_input_json_config (dict): The user's command input JSON to be validated.
#         parent_keys (list, optional): The list of parent keys representing the path to the current level. Default is None.
#         capabilities (dict, optional): A dictionary containing capabilities. Default is None.

#     Returns:
#         list: A list of error messages if any validation rules are violated, or an empty list if the input JSON is valid.
#     """
#     error_msgs = []
#     for key, value in semantic_validation_constant_json.items():
#         current_parent_keys = parent_keys + [key] if parent_keys else [key]
#         print("current_parent_keys", current_parent_keys, key)
#         if isinstance(value, list):
#             error_msg = apply_validation_rule(key, value, command_input_json_config, tuple(current_parent_keys), capabilities)
#             if error_msg:
#                 error_msgs.append(error_msg)
#             print("valuuuuuuuuuuuuuuuuueeeeee", error_msg)
#             llllll
#             # import pdb; pdb.set_trace()
#         elif isinstance(value, dict):
#             if "parent_key_rule" in value:
#                 rule_key = list(value.keys())[1]
#                 rule_result = apply_validation_rule(
#                     key=rule_key,
#                     value=value["parent_key_rule"],
#                     command_input_json_config=command_input_json_config,
#                     parent_key=tuple(current_parent_keys),
#                     capabilities=capabilities,
#                 )
#                 if rule_result:
#                     error_msgs.append(rule_result)
#             else:
#                 error_msgs.extend(validate_json(value, command_input_json_config, current_parent_keys, capabilities))
#                 error_msg = apply_validation_rule(key, value, command_input_json_config, tuple(current_parent_keys), capabilities)
#                 if error_msg:
#                     error_msgs.append(error_msg)
                
#     return error_msgs


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
