"""The base of the view models."""

from pydantic import ConfigDict

from ska_ost_osd.osd.models.defaults import OSDBaseModel

# The largest 32-bit signed integer: served as Mid's
# allowed_channel_count_range_max when the OSD sets no channel limit, which is
# how clients read it
NO_CHANNEL_LIMIT = 2147483647


def legacy_zoom_factors(zoom_factors: list[int]) -> list[int]:
    """Zoom factors as the pre-8.0 responses served them: the multipliers
    2**z, with 1 for no zoom, or ``[0]`` when no zoom is offered.

    :param zoom_factors: the PDM's zoom factors offered, e.g. ``[1, 2, 3]``.
    :return: the served zoom factors, e.g. ``[1, 2, 4, 8]``.
    """
    return [1, *(2**zoom for zoom in zoom_factors)] if zoom_factors else [0]


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
