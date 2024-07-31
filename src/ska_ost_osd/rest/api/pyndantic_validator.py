import re
from typing import List, Optional

from pydantic import BaseModel, model_validator

from ska_ost_osd.osd.constant import ARRAY_ASSEMBLY_PATTERN, OSD_VERSION_PATTERN
from ska_ost_osd.telvalidation.constant import INTERFACE_PATTERN


class OSDModelError(Exception):
    """Custom exception class for validation errors."""

    def __init__(self, errors: List[dict]):
        self.errors = errors
        super().__init__(errors)


class OSDModel(BaseModel):
    cycle_id: Optional[int] = None
    osd_version: Optional[str] = None
    source: Optional[str] = None
    gitlab_branch: Optional[str] = None
    capabilities: Optional[str] = None
    array_assembly: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def validate_combinations(cls, values: dict) -> dict:
        cycle_id = values.get("cycle_id")
        osd_version = values.get("osd_version")
        gitlab_branch = values.get("gitlab_branch")
        capabilities = values.get("capabilities")
        array_assembly = values.get("array_assembly")

        errors = []
        # Validate forbidden combinations
        if gitlab_branch and osd_version:
            errors.append(
                {
                    "msg": "gitlab_branch and osd_version cannot be used together",
                    "value": f"{gitlab_branch}, {osd_version}",
                }
            )
        if cycle_id and array_assembly:
            errors.append(
                {
                    "msg": "cycle_id and array_assembly cannot be used together",
                    "value": f"{cycle_id}, {array_assembly}",
                }
            )

        # Validate either combination
        if not (cycle_id or capabilities):
            errors.append(
                {
                    "msg": "Either cycle_id or capabilities must be provided",
                    "value": f"{cycle_id}, {capabilities}",
                }
            )

        # Validate patterns
        if osd_version and not re.match(OSD_VERSION_PATTERN, osd_version):
            errors.append(
                {"msg": "osd_version value is not valid", "value": osd_version}
            )
        if array_assembly and not re.match(ARRAY_ASSEMBLY_PATTERN, array_assembly):
            errors.append(
                {"msg": "array_assembly value is not valid", "value": array_assembly}
            )
        if errors:
            raise OSDModelError(errors)

        return values


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
