"""Exceptions raised by the query functions in ``ska_ost_osd.osd.queries``."""

from ska_ost_osd.osd.common.constant import Telescope
from ska_ost_osd.osd.common.osd_validation_messages import (
    CAPABILITY_SET_DOESNOT_EXIST_ERROR_MESSAGE,
    CYCLE_ID_ERROR_MESSAGE,
)
from ska_ost_osd.osd.models.observatory_policies import CycleID


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
