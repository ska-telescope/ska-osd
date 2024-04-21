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

    :param QueryParams: abstract class
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
    Class to represent SemanticValidationBody Parameters
    """

    observing_command_input: Dict
    interface: Optional[str] = None
    raise_semantic: Optional[bool] = None
    sources: Optional[List] = None
    osd_data: Optional[Dict] = None


class JsonValidator:
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
        self.validate_required_fields()
        self.validate_invalid_fields()
        self.validate_field_rules()
        self.validate_combinations()

    def validate_invalid_fields(self) -> None:
        invalid_fields = set(self.input_fields) - self.validation_rules["valid_fields"]
        if invalid_fields:
            self.errors[
                "invalid_fields"
            ] = f"These fields are not allowed: {', '.join(invalid_fields)}"

    def validate_required_fields(self) -> None:
        missing_fields = self.validation_rules["required_fields"] - set(
            self.input_fields.keys()
        )
        if missing_fields:
            self.errors[
                "missing_required_fields"
            ] = f"Missing required fields: {', '.join(missing_fields)}"
        self.missing_fields = missing_fields

    def validate_field_rules(self) -> None:
        """
        Validates fields against their specific rules.

        Parameters:
            input_fields (Dict[str, Any]): The fields provided by the user.
            errors (Dict[str, List[str]]): A dictionary to collect error messages.
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
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls.__name__ != "BaseValidationRules":
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
            return cls._instances[cls]
        else:
            return super().__call__(*args, **kwargs)

    def __new__(cls, name, bases, dct):
        error_details = {}
        if bases:
            derived_attributes = {
                attr for attr in dct.keys() if not attr.startswith("__")
            }
            base_class_attributes = {
                attr for attr in dir(bases[0]) if not attr.startswith("__")
            }

            additional_attributes = derived_attributes - base_class_attributes

            if additional_attributes:
                error_details["additional_attributes"] = additional_attributes

            if error_details:
                raise TypeError(error_details)
        return super().__new__(cls, name, bases, dct)


class BaseValidationRules(metaclass=RestrictiveMeta):
    def __init__(
        self,
        valid_fields: Set[str],
        field_rules: Dict[str, Any],
        required_fields: Set[str],
        required_combinations: Dict[str, Any],
        forbidden_combinations: Dict[str, Any],
    ):
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
        Validates input fields and creates an instance using the provided factory function.

        Parameters:
            input_fields (Dict[str, Any]): The fields to validate.
            create_instance_func (Callable): A factory function to create an instance of QueryParams.

        Returns:
            An instance of QueryParams.
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
    def __init__(self):
        # Define validation rules for SemanticValidationBodyParamsValidator
        valid_fields = semantic_validation_rules["valid_fields"]
        field_rules = semantic_validation_rules["field_rules"]
        required_fields = semantic_validation_rules["required_fields"]
        required_combinations = semantic_validation_rules["required_combinations"]
        forbidden_combinations = semantic_validation_rules["forbidden_combinations"]

        # Initialize BaseValidationRules with these validation rules
        super().__init__(
            valid_fields,
            field_rules,
            required_fields,
            required_combinations,
            forbidden_combinations,
        )


class OSDQueryParamsValidator(BaseValidationRules):
    def __init__(self):
        # Define validation rules for OSDQueryParamsValidator
        valid_fields = osd_get_api_rules["valid_fields"]
        field_rules = osd_get_api_rules["field_rules"]
        required_fields = osd_get_api_rules["required_fields"]
        required_combinations = osd_get_api_rules["required_combinations"]
        forbidden_combinations = osd_get_api_rules["forbidden_combinations"]
        self.a = 1

        # Initialize BaseValidationRules with these validation rules
        super().__init__(
            valid_fields,
            field_rules,
            required_fields,
            required_combinations,
            forbidden_combinations,
        )
