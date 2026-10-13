"""The interface for reading the OSD, independent of where it is stored.

A repository reads the OSD from one backend (today the tmdata through a TMData
client; later perhaps a database) and returns reader models. Callers, and the
views, depend only on this interface; the backend's own storage models stay
inside its implementation.
"""

from typing import Literal, Protocol, overload

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


class OSDRepository(Protocol):
    """Reads the OSD's cycles, capability sets, basic capabilities,
    constraints, defaults and subarray templates, and the links between them.

    A method that looks up one item by its key raises a subclass of
    ``OSDQueryError`` (``ska_ost_osd.osd.exceptions``) if there is none.
    """

    # Cycles

    def get_cycle_ids(self) -> list[CycleID]:
        """The cycle IDs, in ascending order."""
        ...

    def get_cycle(self, cycle_id: CycleID) -> Cycle:
        """One cycle. Raises ``CycleNotFoundError`` if there is none."""
        ...

    def get_cycles(self) -> list[Cycle]:
        """Every cycle, in ascending order of ID."""
        ...

    # Per telescope

    @overload
    def get_defaults(self, telescope: Literal[Telescope.MID]) -> MidDefaults: ...

    @overload
    def get_defaults(self, telescope: Literal[Telescope.LOW]) -> LowDefaults: ...

    def get_defaults(self, telescope: Telescope) -> MidDefaults | LowDefaults:
        """A telescope's defaults: Mid's SPFRx defaults or Low's quality
        attribute metrics."""
        ...

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
        """A telescope's basic capabilities: Mid's receiver bands, or Low's
        frequency band and how it is divided into channels."""
        ...

    def get_constraints(self, telescope: Telescope) -> Constraints:
        """A telescope's elevation limits and sun, moon and Jupiter
        avoidance angles."""
        ...

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
        """All of a telescope's capability sets."""
        ...

    @overload
    def get_capability_set(
        self, telescope: Literal[Telescope.MID], name: str
    ) -> MidCapabilitySet: ...

    @overload
    def get_capability_set(
        self, telescope: Literal[Telescope.LOW], name: str
    ) -> LowCapabilitySet: ...

    def get_capability_set(self, telescope: Telescope, name: str) -> CapabilitySet:
        """One capability set, by its telescope and name. Raises
        ``CapabilitySetNotFoundError`` if there is none."""
        ...

    # Joins

    def get_capability_set_templates(
        self, telescope: Telescope, name: str
    ) -> list[SubarrayTemplate]:
        """The subarray templates a capability set offers. Raises
        ``CapabilitySetNotFoundError`` if there is no such capability set."""
        ...

    def get_cycle_capability_sets(
        self, cycle_id: CycleID
    ) -> dict[Telescope, CapabilitySet]:
        """The capability set a cycle offers for each telescope; a telescope
        it does not offer is left out. Raises ``CycleNotFoundError`` if there
        is no such cycle, and ``CapabilitySetNotFoundError`` if the cycle
        names a capability set that does not exist."""
        ...
