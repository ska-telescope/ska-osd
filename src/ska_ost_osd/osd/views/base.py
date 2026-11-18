"""The base of the view models."""

from pydantic import ConfigDict

from ska_ost_osd.osd.models.defaults import OSDBaseModel

# The largest 32-bit signed integer: served as Mid's
# allowed_channel_count_range_max when the OSD sets no channel limit, which is
# how clients read it
NO_CHANNEL_LIMIT = 2147483647


class ConfigurationModel(OSDBaseModel):
    model_config = ConfigDict(
        extra="forbid", validate_default=True, validate_assignment=True
    )
