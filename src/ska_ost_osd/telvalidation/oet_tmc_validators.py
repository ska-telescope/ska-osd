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

import astropy.units as u
import simpleeval
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
SEMANTIC_DATA_GLOBAL_CONSTANT = {}


def get_value_based_on_key(
    input_command_data: dict,
    search_key: str,
    item_populated_list: list,
    parent_key_for_search: str,
    comparison_parent_key: str,
) -> list:
    """
    This function return value which we have to apply semantic validation
    e.g "dish": {
                "receptor_ids": ["0001", "0002"]
            }
    here we are fetching receptor_ids for semantic validation

    :param input_command_data: dictionary containing details of the command
        which needs validation.

    :param search_key: string containing keys of all parameters
        which needs validation.

    :param item_populated_list: list containing all the search values

    :param parent_key_for_search: supporting key to identify proper semantic
        validation key

    :param comparison_parent_key: help to compare parent values.

    :returns: item_populated list

    """
    for key, item in input_command_data.items():
        if (
            parent_key_for_search
            and isinstance(key, str)
            and key == search_key
            and parent_key_for_search == comparison_parent_key
        ):
            item_populated_list.append(item)
        elif isinstance(item, dict):
            get_value_based_on_key(
                item,
                search_key,
                item_populated_list,
                parent_key_for_search,
                comparison_parent_key=key,
            )
        elif isinstance(item, list) and [val for val in item if isinstance(val, dict)]:
            for new_val in item:
                get_value_based_on_key(
                    new_val,
                    search_key,
                    item_populated_list,
                    parent_key_for_search,
                    comparison_parent_key=key,
                )
    # fetch single matched command input value consider for dish
    # "dish": {
    #            "receptor_ids": ["0001", "0002"]
    #        }
    # for receptor_ids it will return ["0001","0002"]
    # value appended list contains
    # multiple value so picked up 0th index value
    item_populated = (
        item_populated_list[0] if len(item_populated_list) > 0 else item_populated_list
    )
    return item_populated


def search_and_return_value_from_basic_capabilities(
    basic_capabilities: dict, search_key: str, rule: str, result: list
) -> list:
    """
    This function returns list of matched key value dict based on rule value
    e.g the updated structure of basic capabilities and rule is below
    capabilities =  {
                "available_receivers": [{
                        "rx_id": "Band_1",
                        "min_frequency_hz": 350000000.0,
                        "max_frequency_hz": 1050000000.0,
                    }],
                "number_ska_dishes": 4
            }
    rule from mid-validation-constant.json
    "freq_min":[
                {
                "rule": "min_frequency_hz <= freq_min <= max_frequency_hz",
                "error": "Invalid input for freq_min"
                }
            ]
    min_frequency_hz and max_frequency_hz rule constraints we are matching from
    capabilities hence output list becomes [{"min_frequency_hz": 350000000.0,
                "max_frequency_hz": 1050000000.0}]

    : param basic_capabilities: capabilities from OSD
    : param search_key: keys from rule file
    : return: return matched capabilities based on rule file keys
    """
    temp_value = {}
    if isinstance(basic_capabilities, dict):
        for key, value in basic_capabilities.items():
            if rule:
                # checking osd_key present in rule or not
                # if it get matched then we are updating into temp dict
                if key in rule:
                    temp_value.update({key: value})
            if isinstance(value, dict):
                search_and_return_value_from_basic_capabilities(
                    value, search_key, rule, result
                )
            if isinstance(value, list):
                for i in value:
                    if isinstance(i, dict):
                        search_and_return_value_from_basic_capabilities(
                            i, search_key, rule, result
                        )
                    if i == search_key:
                        result.append(basic_capabilities)
            if key == search_key or value == search_key:
                result.append(basic_capabilities)
        if temp_value:
            result.append(temp_value)
    return result


def apply_validation_rule(
    key: str,
    value: list,
    command_input_json_config: dict,
    parent_key: str,
    capabilities: dict,
) -> str:
    """
    This is main function which evaluate rules using simpleeval
    if rule is correctly evaluated means given input is valid
    if not then it will return error message.
    :param key: user input key for search.
    :param value: value list contains rule and error.
    :command_input_json_config: command input json from operator.
    :param parent_key: parent key helps to identify correct child key.
    :returns: error message after applying the rule.
    """

    res_value = get_value_based_on_key(
        command_input_json_config,
        key,
        item_populated_list=[],
        parent_key_for_search=parent_key,
        comparison_parent_key=None,
    )
    if res_value:
        # globally initialize semantic data and stored key, value
        # simpleeval library doesn't support passing list, dict, set
        # as parameters to functions.
        SEMANTIC_DATA_GLOBAL_CONSTANT.update({key: res_value})
        eval_functions = simpleeval.DEFAULT_FUNCTIONS.copy()
        eval_functions.update(
            length=return_length,
            value=return_value_from_global_constant,
        )
        error_msgs = []  # Initialize an empty error message
        for rule_data in value:
            try:
                rule_key_dict = search_and_return_value_from_basic_capabilities(
                    basic_capabilities=capabilities,
                    search_key=None,
                    rule=rule_data["rule"],
                    result=[],
                )
                names = {}
                eval_new_data = []
                if len(rule_key_dict) > 1:
                    # below code is written to fetch multiple rule keys from
                    # osd API e.g for frequency min, max rule
                    # min_frequency_hz <= freq_min <= max_frequency_hz
                    # we require to fetch 2 keys same time
                    # from OSD and apply eval
                    for i in rule_key_dict:
                        names = {key: res_value}
                        names = {**names, **i}
                        eval_data1 = EvalWithCompoundTypes(
                            functions=eval_functions, names=names
                        ).eval(rule_data["rule"])
                        if eval_data1 is False or (
                            not isinstance(eval_data1, bool) and len(eval_data1) > 0
                        ):
                            eval_new_data.append(False)
                        else:
                            eval_new_data.append(True)
                else:
                    # created new rule dict based on OSD keys
                    # this is based on single rule key from OSD
                    # e.g number_ska_dishes is single key value we
                    # are fetching from OSD.
                    rule_key_dict_new = {}
                    if rule_key_dict:
                        rule_key_dict_new = rule_key_dict[0]
                    if "dependency_key" in rule_data:
                        names = {
                            key: key,
                            rule_data["dependency_key"]: rule_data["dependency_key"],
                        }
                    elif isinstance(res_value, list):
                        names = {key: key}
                        names = {**names, **rule_key_dict_new}
                    else:
                        names = {key: res_value}
                        names = {**names, **rule_key_dict_new}
                    eval_data = EvalWithCompoundTypes(
                        functions=eval_functions, names=names
                    ).eval(rule_data["rule"])

                    if eval_data is False or (
                        not isinstance(eval_data, bool) and len(eval_data) > 0
                    ):
                        if rule_key_dict_new:
                            # find {number_ska_dishes} this value
                            # and replaced with {}.
                            # python string format can't work
                            # with {number_ska_dishes}.
                            error_msgs.append(
                                rule_data["error"].format(**rule_key_dict_new)
                            )  # Append the error messages from OSD based keys
                        else:
                            error_msgs.append(
                                rule_data["error"]
                            )  # Append the error message

                if eval_new_data and True not in eval_new_data:
                    error_msgs.append(rule_data["error"])  # Append the error message
            except KeyError as key_error:
                logging.error(key_error)
                raise SchemanticValdidationKeyError(
                    message="Invalid rule and error key passed"
                )
        return "\n".join(error_msgs)  # Return the combined error message


def validate_json(
    semantic_validate_constant_json: dict,
    command_input_json_config: dict,
    error_msg_list: list,
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
            # key helps to apply rule on child
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
            validate_json(
                value,
                command_input_json_config,
                error_msg_list,
                parent_key,
                capabilities,
            )
    return error_msg_list


def return_length(key, is_distinct=False):
    """
    this function is created to just return length of element.
    simpleeval library not supported default length on list, tuple, set
    so we need to create separate method and pass it simpleeval as a function.
    :param key: semantic validate key.
    """
    if is_distinct:
        return len(set(SEMANTIC_DATA_GLOBAL_CONSTANT[key]))

    return len(SEMANTIC_DATA_GLOBAL_CONSTANT[key])


def return_value_from_global_constant(key):
    """
    this fucntion is created to just return value of element from semantic
    data global constant.
    :param key: semantic validate key.
    """
    return SEMANTIC_DATA_GLOBAL_CONSTANT[key]


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
