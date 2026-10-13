"""The base of the view models."""

from pydantic import ConfigDict

from ska_ost_osd.osd.models.defaults import OSDBaseModel


class ConfigurationModel(OSDBaseModel):
    model_config = ConfigDict(
        extra="forbid", validate_default=True, validate_assignment=True
    )
