"""The base of the view models."""

from pydantic import ConfigDict

from ska_ost_osd.osd.models.defaults import OSDBaseModel


class ConfigurationModel(OSDBaseModel):
    # serialize_by_alias: a view serialises with the names its consumer
    # reads (e.g. the PHT's Mid and Low) without the caller passing
    # by_alias=True
    model_config = ConfigDict(
        extra="forbid",
        validate_default=True,
        validate_assignment=True,
        serialize_by_alias=True,
    )
