"""The OSD repository backed by the tmdata, read through a TMData client."""

from typing import Literal, overload

from ska_telmodel_client import TMData

from ska_ost_osd.osd import queries
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
        return queries.get_cycle_ids(self._tmdata)

    def get_cycle(self, cycle_id: CycleID) -> Cycle:
        return queries.get_cycle(self._tmdata, cycle_id)

    def get_cycles(self) -> list[Cycle]:
        return queries.get_cycles(self._tmdata)

    # Per telescope

    @overload
    def get_defaults(self, telescope: Literal[Telescope.MID]) -> MidDefaults: ...

    @overload
    def get_defaults(self, telescope: Literal[Telescope.LOW]) -> LowDefaults: ...

    def get_defaults(self, telescope: Telescope) -> MidDefaults | LowDefaults:
        return queries.get_defaults(self._tmdata, telescope)

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
        return queries.get_basic_capabilities(self._tmdata, telescope)

    def get_constraints(self, telescope: Telescope) -> Constraints:
        return queries.get_constraints(self._tmdata, telescope)

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
        return queries.get_capability_sets(self._tmdata, telescope)

    @overload
    def get_capability_set(
        self, telescope: Literal[Telescope.MID], name: str
    ) -> MidCapabilitySet: ...

    @overload
    def get_capability_set(
        self, telescope: Literal[Telescope.LOW], name: str
    ) -> LowCapabilitySet: ...

    def get_capability_set(self, telescope: Telescope, name: str) -> CapabilitySet:
        return queries.get_capability_set(self._tmdata, telescope, name)

    # Joins

    def get_subarray_templates(
        self, telescope: Telescope, capability_set: str
    ) -> list[SubarrayTemplate]:
        return queries.get_subarray_templates(self._tmdata, telescope, capability_set)

    def get_cycle_capability_sets(
        self, cycle_id: CycleID
    ) -> dict[Telescope, CapabilitySet]:
        raise NotImplementedError
