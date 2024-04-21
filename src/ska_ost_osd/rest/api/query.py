from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Type

from ska_ost_osd.rest.api.api_validation_rule import (
    osd_get_api_rules,
    semantic_validation_rules,
)


@dataclass
class QueryParams:
    """
    QueryParams is an abstract class
    """


@dataclass
class OSDUserQuery(QueryParams):
    """
    Class to represent a user query.

    This class stores parameters for querying OSD data. It inherits
    from the QueryParams base class to validate and parse query
    string parameters.

    :param cycle_id (int): ID of the cycle.
    :param osd_version (str): Version of OSD.
    :param source (str): Source of the query.
    :param gitlab_branch (str): Branch in GitLab.
    :param capabilities (str): Capabilities information.
    :param array_assembly (str): Assembly of the array.
    """

    cycle_id: int = None
    osd_version: str = None
    source: str = None
    gitlab_branch: str = None
    capabilities: str = None
    array_assembly: str = None


@dataclass
class SemanticValidationBodyParams:
    """
    Class to represent SemanticValidationBody parameters.

    :param observing_command_input (Dict): Input for observing command.
    :param interface (Optional[str]): Interface information.
    :param raise_semantic (Optional[bool]): Flag to raise semantic errors.
    :param sources (Optional[List]): List of sources.
    :param osd_data (Optional[Dict]): OSD data information.
    """

    observing_command_input: Dict
    interface: Optional[str] = None
    raise_semantic: Optional[bool] = None
    sources: Optional[List] = None
    osd_data: Optional[Dict] = None


class JsonValidator:
    """
    Class to validate JSON input against validation rules.
    """

    def __init__(self):
        self.validation_rules = None
        self.input_fields = None
        self.raise_exception = None
        self.errors = {}
        self.missing_fields = set()

    def process_input(
        self,
        input_fields: Dict[str, Any],
        validation_rules,
        create_instance_func: Type[QueryParams],
        raise_exception: bool = False,
    ) -> QueryParams:
        """
        Process input fields and validate them against rules.

        :param input_fields (Dict[str, Any]): Input fields to validate.
        :param validation_rules: Validation rules.
        :param create_instance_func (Type[QueryParams]): Factory function to create an instance of QueryParams.
        :param raise_exception (bool): Flag to raise exception on validation error.
        :return: Instance of QueryParams.
        """

        self.validation_rules = validation_rules
        self.input_fields = input_fields
        self.validate_fields()
        self.raise_exception = raise_exception
        if self.missing_fields and not self.raise_exception:
            for field in self.missing_fields:
                self.input_fields[field] = None

        if self.errors and self.raise_exception:
            raise ValueError(self.errors)

        temp_obj = create_instance_func(**input_fields)
        return temp_obj, self.errors

    def validate_fields(self) -> None:
        """
        Validate input fields against rules.
        """
        self.validate_required_fields()
        self.validate_invalid_fields()
        self.validate_field_rules()
        self.validate_combinations()

    def validate_invalid_fields(self) -> None:
        """
        Validate invalid fields.
        """
        invalid_fields = set(self.input_fields) - self.validation_rules["valid_fields"]
        if invalid_fields:
            self.errors[
                "invalid_fields"
            ] = f"These fields are not allowed: {', '.join(invalid_fields)}"

    def validate_required_fields(self) -> None:
        """
        Validate required fields.
        """
        
        missing_fields = set(self.validation_rules["required_fields"]) - set(self.input_fields.keys())
        if missing_fields:
            self.errors[
                "missing_required_fields"
            ] = f"Missing required fields: {', '.join(missing_fields)}"
        self.missing_fields = missing_fields

    def validate_field_rules(self) -> None:
        """
        Validate field rules.
        """
        for field, rules in self.validation_rules["field_rules"].items():
            if field in self.input_fields:
                field_value = self.input_fields[field]
                for rule in rules:
                    error_msg = (
                        "value" + " " + str(field_value) + " for " + rule.error_msg
                    )
                    if not rule.rule(field_value):
                        if field not in self.errors:  # first error
                            self.errors[field] = error_msg
                        else:
                            if isinstance(self.errors[field], list):
                                self.errors[field].append(error_msg)
                            else:  # string, so only one error
                                self.errors[field] = list(self.errors[field])
                                self.errors[field].append(error_msg)

    def validate_combinations(self) -> None:
        """
        Validate combinations of fields.
        """
        for comb_name, keys in self.validation_rules["required_combinations"].items():
            if not all(k in self.input_fields for k in keys):
                self.errors[
                    comb_name
                ] = f"Combination {comb_name} is required but missing one or more keys."

        # Forbidden combinations
        for comb_name, keys in self.validation_rules["forbidden_combinations"].items():
            if all(k in self.input_fields for k in keys):
                self.errors[
                    comb_name
                ] = f"Combination {comb_name} should not be present together."


class RestrictiveMeta(type):
    """
    Metaclass for creating singleton instances.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        # code for singleton
        if cls.__name__ != "BaseValidationRules":
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
            return cls._instances[cls]
        else:
            return super().__call__(*args, **kwargs)


class BaseValidationRules(metaclass=RestrictiveMeta):
    """
    Base class for defining validation rules for input data.

    This class serves as a foundation for defining validation rules that can be applied to various types of input data.
    """

    def __init__(
        self,
        valid_fields: Set[str],
        field_rules: Dict[str, Any],
        required_fields: Set[str],
        required_combinations: Dict[str, Any],
        forbidden_combinations: Dict[str, Any],
    ):
        """
        Initialize BaseValidationRules class.

        :param valid_fields (Set[str]): Set of valid fields.
        :param field_rules (Dict[str, Any]): Dictionary containing field rules.
        :param required_fields (Set[str]): Set of required fields.
        :param required_combinations (Dict[str, Any]): Dictionary containing required field combinations.
        :param forbidden_combinations (Dict[str, Any]): Dictionary containing forbidden field combinations.

        """
        self.valid_fields = valid_fields
        self.field_rules = field_rules
        self.required_fields = required_fields
        self.required_combinations = required_combinations
        self.forbidden_combinations = forbidden_combinations

    def process_input(
        self,
        input_fields: Dict[str, Any],
        create_instance_func: Type[QueryParams],
        raise_exception: bool = False,
    ) -> QueryParams:
        """
        Process input fields and create an instance of QueryParams.

        :param input_fields (Dict[str, Any]): Input fields to validate.
        :param create_instance_func (Type[QueryParams]): Factory function to create an instance of QueryParams.
        :param raise_exception (bool): Flag to raise exception on validation error.
        :return: Instance of QueryParams.
        """
        validation_rules = {
            "valid_fields": self.valid_fields,
            "field_rules": self.field_rules,
            "required_fields": self.required_fields,
            "required_combinations": self.required_combinations,
            "forbidden_combinations": self.forbidden_combinations,
        }
        return JsonValidator().process_input(
            input_fields, validation_rules, create_instance_func, raise_exception
        )


class SemanticValidationBodyParamsValidator(BaseValidationRules):
    """
    Class to validate SemanticValidationBodyParams.
    """

    def __init__(self):
        """
        Initialize SemanticValidationBodyParamsValidator class.

        Initializes validation rules for SemanticValidationBodyParamsValidator using custom rules from api_validation_rules.

        Instance Variables:
            valid_fields (Set[str]): Set of valid fields.
            field_rules (Dict[str, Any]): Dictionary containing field rules.
            required_fields (Set[str]): Set of required fields.
            required_combinations (Dict[str, Any]): Dictionary containing required field combinations.
            forbidden_combinations (Dict[str, Any]): Dictionary containing forbidden field combinations.
        """
        self.valid_fields = semantic_validation_rules["valid_fields"]
        self.field_rules = semantic_validation_rules["field_rules"]
        self.required_fields = semantic_validation_rules["required_fields"]
        self.required_combinations = semantic_validation_rules["required_combinations"]
        self.forbidden_combinations = semantic_validation_rules[
            "forbidden_combinations"
        ]

        super().__init__(
            self.valid_fields,
            self.field_rules,
            self.required_fields,
            self.required_combinations,
            self.forbidden_combinations,
        )


class OSDQueryParamsValidator(BaseValidationRules):
    """
    Class to validate OSDQueryParams.
    """

    def __init__(self):
        """
        Initialize OSDQueryParamsValidator class.

        Initializes validation rules for OSDQueryParamsValidator using custom rules from api_validation_rules.

        Instance Variables:
            valid_fields (Set[str]): Set of valid fields.
            field_rules (Dict[str, Any]): Dictionary containing field rules.
            required_fields (Set[str]): Set of required fields.
            required_combinations (Dict[str, Any]): Dictionary containing required field combinations.
            forbidden_combinations (Dict[str, Any]): Dictionary containing forbidden field combinations.
        """
        # Define validation rules for OSDQueryParamsValidator
        self.valid_fields = osd_get_api_rules["valid_fields"]
        self.field_rules = osd_get_api_rules["field_rules"]
        self.required_fields = osd_get_api_rules["required_fields"]
        self.required_combinations = osd_get_api_rules["required_combinations"]
        self.forbidden_combinations = osd_get_api_rules["forbidden_combinations"]
        self.a = 1
        # Initialize BaseValidationRules with these validation rules
        super().__init__(
            self.valid_fields,
            self.field_rules,
            self.required_fields,
            self.required_combinations,
            self.forbidden_combinations,
        )
