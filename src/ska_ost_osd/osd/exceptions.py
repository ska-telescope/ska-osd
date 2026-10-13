"""Exceptions raised by the OSD repository and the reader models when a key
has no data."""

from ska_ost_osd.osd.common.constant import Telescope
from ska_ost_osd.osd.common.osd_validation_messages import (
    BAND5B_SUBBAND_DOESNOT_EXIST_ERROR_MESSAGE,
    CAPABILITY_SET_DOESNOT_EXIST_ERROR_MESSAGE,
    CYCLE_ID_ERROR_MESSAGE,
    FREQUENCY_BAND_DOESNOT_EXIST_ERROR_MESSAGE,
)
from ska_ost_osd.osd.models.cycles import CycleID


class OSDQueryError(Exception):
    """Base class for errors raised while querying the OSD tmdata."""


class CycleNotFoundError(OSDQueryError, LookupError):
    """There is no cycle with the requested ID.

    :param cycle_id: the cycle ID requested.
    :param available_cycle_ids: the cycle IDs that do exist.
    """

    def __init__(self, cycle_id: CycleID, available_cycle_ids: list[CycleID]):
        self.cycle_id = cycle_id
        self.available_cycle_ids = available_cycle_ids
        super().__init__(
            CYCLE_ID_ERROR_MESSAGE.format(
                cycle_id, ",".join(str(cycle) for cycle in available_cycle_ids)
            )
        )


class CapabilitySetNotFoundError(OSDQueryError, LookupError):
    """The telescope has no capability set with the requested name.

    :param telescope: the telescope searched.
    :param name: the capability set name requested.
    :param available_names: the names of the telescope's capability sets.
    """

    def __init__(self, telescope: Telescope, name: str, available_names: list[str]):
        self.telescope = telescope
        self.name = name
        self.available_names = available_names
        super().__init__(
            CAPABILITY_SET_DOESNOT_EXIST_ERROR_MESSAGE.format(
                name, telescope, ", ".join(available_names)
            )
        )


class FrequencyBandNotFoundError(OSDQueryError, LookupError):
    """Mid has no receiver band with the requested ID.

    :param rx_id: the band ID requested, e.g. ``"Band_2"``.
    :param available_rx_ids: the IDs of Mid's bands.
    """

    def __init__(self, rx_id: str, available_rx_ids: list[str]):
        self.rx_id = rx_id
        self.available_rx_ids = available_rx_ids
        super().__init__(
            FREQUENCY_BAND_DOESNOT_EXIST_ERROR_MESSAGE.format(
                rx_id, ", ".join(available_rx_ids)
            )
        )


class Band5bSubbandNotFoundError(OSDQueryError, LookupError):
    """The band has no Band 5b sub-band with the requested number.

    :param rx_id: the band searched.
    :param sub_band: the sub-band number requested.
    :param available_sub_bands: the band's sub-band numbers.
    """

    def __init__(self, rx_id: str, sub_band: int, available_sub_bands: list[int]):
        self.rx_id = rx_id
        self.sub_band = sub_band
        self.available_sub_bands = available_sub_bands
        super().__init__(
            BAND5B_SUBBAND_DOESNOT_EXIST_ERROR_MESSAGE.format(
                sub_band,
                rx_id,
                ", ".join(str(n) for n in available_sub_bands) or "none",
            )
        )
