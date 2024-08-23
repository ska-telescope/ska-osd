import re
from typing import List, Optional

from pydantic import BaseModel, model_validator

from ska_ost_osd.telvalidation.constant import INTERFACE_PATTERN


class SemanticModelError(Exception):
    """Custom exception class for validation errors."""

    def __init__(self, errors: List[dict]):
        self.errors = errors
        super().__init__(errors)


class SemanticModel(BaseModel):
    observing_command_input: dict
    interface: Optional[str] = None
    raise_semantic: Optional[bool] = None
    array_assembly: Optional[str] = None
    osd_data: Optional[dict] = None
    tm_data: Optional[object] = None

    @model_validator(mode="before")
    @classmethod
    def validate_semantic_combinations(cls, values: dict) -> dict:
        interface = values.get("interface")

        errors = []
        if interface and not re.match(INTERFACE_PATTERN, interface):
            errors.append({"msg": "interface is not valid", "value": interface})
        if errors:
            raise SemanticModelError(errors)
        return values
