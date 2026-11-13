"""The interface for reading the OSD, independent of where it is stored.

A repository reads the OSD from one backend (today the tmdata through a TMData
client; later perhaps a database) and returns reader models. Callers, and the
views, depend only on this interface; the backend's own storage models stay
inside its implementation.
"""

from typing import Literal, Protocol, overload

from ska_ost_osd.osd.common.constant import Telescope
from ska_ost_osd.osd.models.capabilities import (
    Capabilities,
    LowBasicCapabilities,
    LowCapabilities,
    MidBasicCapabilities,
    MidCapabilities,
)
from ska_ost_osd.osd.models.constraints import Constraints
from ska_ost_osd.osd.models.cycles import Cycle, PolicyType
from ska_ost_osd.osd.models.defaults import LowDefaults, MidDefaults
from ska_ost_osd.osd.models.subarray_templates import SubarrayTemplate


class OSDRepository(Protocol):
    """Reads the OSD's cycles, capabilities, basic capabilities,
    constraints, defaults and subarray templates, and the links between them.

    A method that looks up one item by its key raises a subclass of
    ``OSDQueryError`` (``ska_ost_osd.osd.exceptions``) if there is none.
    """

    # Cycles

    def get_cycle_ids(self) -> list[str]:
        """The cycle IDs, in ascending order."""
        ...

    def get_cycle(self, cycle_id: str) -> Cycle:
        """One cycle. Raises ``CycleNotFoundError`` if there is none."""
        ...

    def get_cycles(self) -> list[Cycle]:
        """Every cycle, in ascending order of ID."""
        ...

    # Per telescope

    @overload
    def get_defaults(self, telescope: Literal[Telescope.SKA_MID]) -> MidDefaults: ...

    @overload
    def get_defaults(self, telescope: Literal[Telescope.SKA_LOW]) -> LowDefaults: ...

    def get_defaults(self, telescope: Telescope) -> MidDefaults | LowDefaults:
        """A telescope's defaults: Mid's SPFRx defaults or Low's quality
        attribute metrics."""
        ...

    @overload
    def get_basic_capabilities(
        self, telescope: Literal[Telescope.SKA_MID]
    ) -> MidBasicCapabilities: ...

    @overload
    def get_basic_capabilities(
        self, telescope: Literal[Telescope.SKA_LOW]
    ) -> LowBasicCapabilities: ...

    def get_basic_capabilities(
        self, telescope: Telescope
    ) -> MidBasicCapabilities | LowBasicCapabilities:
        """A telescope's basic capabilities: Mid's receiver bands, or Low's
        frequency band and how it is divided into channels, and the
        telescope's elevation limits."""
        ...

    def get_constraints(self, telescope: Telescope) -> Constraints:
        """A telescope's elevation limits and sun, moon and Jupiter
        avoidance angles."""
        ...

    # Capability sets

    @overload
    def get_array_assembly_capabilities(
        self, telescope: Literal[Telescope.SKA_MID]
    ) -> list[MidCapabilities]: ...

    @overload
    def get_array_assembly_capabilities(
        self, telescope: Literal[Telescope.SKA_LOW]
    ) -> list[LowCapabilities]: ...

    def get_array_assembly_capabilities(
        self, telescope: Telescope
    ) -> list[MidCapabilities] | list[LowCapabilities]:
        """The capabilities of each of a telescope's array assemblies, with no
        policy applied."""
        ...

    @overload
    def get_capabilities(
        self,
        telescope: Literal[Telescope.SKA_MID],
        array_assembly: str,
        policy_id: str | None = None,
    ) -> MidCapabilities: ...

    @overload
    def get_capabilities(
        self,
        telescope: Literal[Telescope.SKA_LOW],
        array_assembly: str,
        policy_id: str | None = None,
    ) -> LowCapabilities: ...

    def get_capabilities(
        self, telescope: Telescope, array_assembly: str, policy_id: str | None = None
    ) -> Capabilities:
        """An array assembly's capabilities, with a policy's applied if one is
        given, named after the policy or else the array assembly. Raises
        ``ArrayAssemblyNotFoundError`` if there is no such array assembly, and
        ``FileNotFoundError`` if there is no such policy."""
        ...

    # Joins

    def get_subarray_templates(
        self, telescope: Telescope, array_assembly: str
    ) -> list[SubarrayTemplate]:
        """The subarray templates an array assembly offers. Raises
        ``ArrayAssemblyNotFoundError`` if there is no such array assembly."""
        ...

    def get_cycle_capabilities(
        self, cycle_id: str
    ) -> dict[Telescope, dict[PolicyType, Capabilities]]:
        """The capabilities a cycle offers for each telescope and policy type:
        the telescope's array assembly with that type's policy applied. A
        telescope the cycle does not offer is left out. Raises
        ``CycleNotFoundError`` if there is no such cycle,
        ``ArrayAssemblyNotFoundError`` if the cycle names an array assembly
        that does not exist, and ``FileNotFoundError`` if it names a policy
        that does not exist."""
        ...
