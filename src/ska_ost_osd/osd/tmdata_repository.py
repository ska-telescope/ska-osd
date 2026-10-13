"""The OSD repository backed by the tmdata, read through a TMData client."""

from typing import Literal, overload

from ska_telmodel_client import TMData

from ska_ost_osd.osd.common.constant import Telescope
from ska_ost_osd.osd.models.capabilities import (
    CapabilitySet,
    LowBasicCapabilities,
    LowCapabilitySet,
    MidBasicCapabilities,
    MidCapabilitySet,
)
from ska_ost_osd.osd.models.configuration import Constraints
from ska_ost_osd.osd.models.cycles import Cycle, CycleID
from ska_ost_osd.osd.models.defaults import LowDefaults, MidDefaults
from ska_ost_osd.osd.models.subarray_templates import SubarrayTemplate


class TMDataRepository:
    """Implements ``OSDRepository`` by reading the tmdata through a TMData
    client.

    :param tmdata: the TMData client to read from.
    """

    def __init__(self, tmdata: TMData):
        self._tmdata = tmdata

    # Cycles

    def get_cycle_ids(self) -> list[CycleID]:
        raise NotImplementedError

    def get_cycle(self, cycle_id: CycleID) -> Cycle:
        raise NotImplementedError

    def get_cycles(self) -> list[Cycle]:
        raise NotImplementedError

    # Per telescope

    @overload
    def get_defaults(self, telescope: Literal[Telescope.MID]) -> MidDefaults: ...

    @overload
    def get_defaults(self, telescope: Literal[Telescope.LOW]) -> LowDefaults: ...

    def get_defaults(self, telescope: Telescope) -> MidDefaults | LowDefaults:
        raise NotImplementedError

    @overload
    def get_basic_capabilities(
        self, telescope: Literal[Telescope.MID]
    ) -> MidBasicCapabilities: ...

    @overload
    def get_basic_capabilities(
        self, telescope: Literal[Telescope.LOW]
    ) -> LowBasicCapabilities: ...

    def get_basic_capabilities(
        self, telescope: Telescope
    ) -> MidBasicCapabilities | LowBasicCapabilities:
        raise NotImplementedError

    def get_constraints(self, telescope: Telescope) -> Constraints:
        raise NotImplementedError

    # Capability sets

    @overload
    def get_capability_sets(
        self, telescope: Literal[Telescope.MID]
    ) -> list[MidCapabilitySet]: ...

    @overload
    def get_capability_sets(
        self, telescope: Literal[Telescope.LOW]
    ) -> list[LowCapabilitySet]: ...

    def get_capability_sets(self, telescope: Telescope) -> list[CapabilitySet]:
        raise NotImplementedError

    @overload
    def get_capability_set(
        self, telescope: Literal[Telescope.MID], name: str
    ) -> MidCapabilitySet: ...

    @overload
    def get_capability_set(
        self, telescope: Literal[Telescope.LOW], name: str
    ) -> LowCapabilitySet: ...

    def get_capability_set(self, telescope: Telescope, name: str) -> CapabilitySet:
        raise NotImplementedError

    # Joins

    def get_capability_set_templates(
        self, telescope: Telescope, name: str
    ) -> list[SubarrayTemplate]:
        raise NotImplementedError

    def get_cycle_capability_sets(
        self, cycle_id: CycleID
    ) -> dict[Telescope, CapabilitySet]:
        raise NotImplementedError
