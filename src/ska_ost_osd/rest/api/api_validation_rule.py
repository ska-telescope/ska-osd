import re
from collections import namedtuple

from ska_ost_osd.osd.constant import ARRAY_ASSEMBLY_PATTERN, OSD_VERSION_PATTERN
from ska_ost_osd.telvalidation.constant import INTERFACE_PATTERN

FieldRule = namedtuple("FieldRule", ["rule", "error_msg"])

# Semantic Validation API Validation Rules
semantic_validation_rules = {
    "valid_fields": {
        "observing_command_input",
        "interface",
        "raise_semantic",
        "sources",
        "osd_data",
    },
    "required_fields": {"observing_command_input"},
    "required_combinations": {},
    "forbidden_combinations": {},
    "field_rules": {
        "interface": [
            FieldRule(
                lambda value: isinstance(value, str), "interface must be a string"
            ),
            FieldRule(
                lambda value: re.match(INTERFACE_PATTERN, value),
                "interface is not valid",
            ),
        ],
        "raise_semantic": [
            FieldRule(
                lambda value: isinstance(value, bool),
                "raise_semantic is not a boolean value ",
            )
        ],
        "sources": [
            FieldRule(lambda value: isinstance(value, str), "sources must be a string"),
        ],
        "osd_data": [
            FieldRule(lambda value: isinstance(value, dict), "osd_data must be a dict")
        ],
    },
}


# OSD GET API Validation Rules
osd_get_api_rules = {
    "valid_fields": {
        "cycle_id",
        "osd_version",
        "source",
        "gitlab_branch",
        "capabilities",
        "array_assembly",
    },
    "required_fields": {},
    "required_combinations": {},
    "forbidden_combinations": {
        "gitlab_branch_and_osd_version": ["gitlab_branch", "osd_version"],
        "cycle_id_and_array_assembly": ["cycle_id", "array_assembly"],
    },
    "field_rules": {
        "cycle_id": [
            FieldRule(
                lambda value: isinstance(value, int), "cycle_id must be an integer"
            ),
            FieldRule(
                lambda value: isinstance(value, int), "cycle_id must be an integer"
            ),
        ],
        "osd_version": [
            FieldRule(
                lambda value: isinstance(value, str), "osd_version must be a string"
            ),
            FieldRule(
                lambda value: re.match(OSD_VERSION_PATTERN, value),
                "osd_version is not valid",
            ),
        ],
        "source": [
            FieldRule(lambda value: isinstance(value, str), "source must be a string")
        ],
        "gitlab_branch": [
            FieldRule(
                lambda value: isinstance(value, str), "gitlab_branch must be a string"
            )
        ],
        "capabilities": [
            FieldRule(
                lambda value: isinstance(value, str), "capabilities must be a string"
            )
        ],
        "array_assembly": [
            FieldRule(
                lambda value: isinstance(value, str), "array_assembly must be a string"
            ),
            FieldRule(
                lambda value: re.match(ARRAY_ASSEMBLY_PATTERN, value),
                "array_assembly value is not valid",
            ),
        ],
    },
}
