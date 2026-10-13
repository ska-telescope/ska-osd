"""The OSD repository backed by the tmdata, read through a TMData client."""

from fnmatch import fnmatchcase
from typing import Literal, overload

from ska_telmodel_client import TMData

from ska_ost_osd.osd import queries
from ska_ost_osd.osd.common.constant import Telescope
from ska_ost_osd.osd.exceptions import CapabilitySetNotFoundError, CycleNotFoundError
from ska_ost_osd.osd.models.capabilities import (
    CapabilitySet,
    LowBasicCapabilities,
    LowCapabilitySet,
    MidBasicCapabilities,
    MidCapabilitySet,
)
from ska_ost_osd.osd.models.configuration import Constraints
from ska_ost_osd.osd.models.cycles import Cycle, CycleFile, CycleID
from ska_ost_osd.osd.models.defaults import LowDefaults, MidDefaults
from ska_ost_osd.osd.models.subarray_templates import SubarrayTemplate

_DEFAULTS_MODELS = {
    Telescope.MID: MidDefaults,
    Telescope.LOW: LowDefaults,
}

# The fields of a cycle's telescope_capabilities, by telescope
_CYCLE_TELESCOPE_FIELDS = {
    Telescope.MID: "ska_mid",
    Telescope.LOW: "ska_low",
}


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
        cycle_ids = self.get_cycle_ids()
        if cycle_id not in cycle_ids:
            raise CycleNotFoundError(cycle_id, cycle_ids)
        return self._to_cycle(queries.get_cycle_file(self._tmdata, cycle_id))

    def get_cycles(self) -> list[Cycle]:
        return [
            self._to_cycle(queries.get_cycle_file(self._tmdata, cycle_id))
            for cycle_id in self.get_cycle_ids()
        ]

    # Per telescope

    @overload
    def get_defaults(self, telescope: Literal[Telescope.MID]) -> MidDefaults: ...

    @overload
    def get_defaults(self, telescope: Literal[Telescope.LOW]) -> LowDefaults: ...

    def get_defaults(self, telescope: Telescope) -> MidDefaults | LowDefaults:
        return _DEFAULTS_MODELS[telescope].model_validate(
            queries.get_telescope_defaults(self._tmdata, telescope),
            from_attributes=True,
        )

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
        return queries.get_telescope_capabilities(
            self._tmdata, telescope
        ).basic_capabilities

    def get_constraints(self, telescope: Telescope) -> Constraints:
        return Constraints.combine(
            queries.get_telescope_capabilities(self._tmdata, telescope),
            queries.get_telescope_defaults(self._tmdata, telescope),
        )

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
        return queries.get_telescope_capabilities(self._tmdata, telescope).subarrays

    @overload
    def get_capability_set(
        self, telescope: Literal[Telescope.MID], name: str
    ) -> MidCapabilitySet: ...

    @overload
    def get_capability_set(
        self, telescope: Literal[Telescope.LOW], name: str
    ) -> LowCapabilitySet: ...

    def get_capability_set(self, telescope: Telescope, name: str) -> CapabilitySet:
        capability_sets = self.get_capability_sets(telescope)
        for capability_set in capability_sets:
            if capability_set.name == name:
                return capability_set
        raise CapabilitySetNotFoundError(
            telescope, name, [capability_set.name for capability_set in capability_sets]
        )

    # Joins

    def get_subarray_templates(
        self, telescope: Telescope, capability_set: str
    ) -> list[SubarrayTemplate]:
        """A template belongs to the capability set when its name matches one
        of the set's ``subarray_templates`` patterns (e.g. ``"*_AA2"``) and
        starts with the set's telescope (e.g. ``"MID_"``). A pattern alone is
        not enough: ``"*_AA2"`` matches both telescopes' AA2 templates."""
        patterns = (
            self.get_capability_set(telescope, capability_set).subarray_templates or []
        )
        prefix = f"{telescope.value.upper()}_"
        return [
            template
            for template in queries.get_subarray_template_library(
                self._tmdata
            ).templates
            if template.name.startswith(prefix)
            and any(fnmatchcase(template.name, pattern) for pattern in patterns)
        ]

    def get_cycle_capability_sets(
        self, cycle_id: CycleID
    ) -> dict[Telescope, CapabilitySet]:
        offered = self.get_cycle(cycle_id).telescope_capabilities
        return {
            telescope: self.get_capability_set(telescope, name)
            for telescope, field in _CYCLE_TELESCOPE_FIELDS.items()
            if (name := getattr(offered, field)) is not None
        }

    # Storage to reader models

    @staticmethod
    def _to_cycle(cycle_file: CycleFile) -> Cycle:
        return Cycle.model_validate(cycle_file, from_attributes=True)
