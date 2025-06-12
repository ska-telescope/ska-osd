import re
from typing import Optional

from pydantic import BaseModel, model_validator

from ska_ost_osd.common.constant import INTERFACE_PATTERN


class SemanticModel(BaseModel):
    observing_command_input: dict
    interface: Optional[str] = None
    raise_semantic: Optional[bool] = True
    array_assembly: Optional[str] = None
    osd_data: Optional[dict] = None
    tm_data: Optional[object] = None

    @model_validator(mode="before")
    @classmethod
    def validate_semantic_combinations(cls, values: dict) -> dict:
        errors = []
        # Validate that observing_command_input is present and is a dictionary
        if "observing_command_input" not in values or not isinstance(
            values.get("observing_command_input"), dict
        ):
            errors.append(
                {"field": "observing_command_input", "msg": "This field is required"}
            )

        else:
            interface = values.get("interface")
            if interface and not isinstance(interface, str):
                errors.append(
                    {"field": "interface", "msg": "Interface must be a string"}
                )
            elif interface and not re.match(INTERFACE_PATTERN, interface):
                errors.append(
                    {
                        "field": "interface",
                        "msg": f"Interface must match pattern: {INTERFACE_PATTERN}",
                    }
                )

        if errors:
            raise ValueError(errors)

        return values
