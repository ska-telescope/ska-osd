"""The OSD repository backed by the tmdata, read through a TMData client."""

from typing import Literal, overload

from ska_telmodel_client import TMData

from ska_ost_osd.osd.adapters.tmdata import storage
from ska_ost_osd.osd.adapters.tmdata.models import CycleFile
from ska_ost_osd.osd.common.constant import Telescope
from ska_ost_osd.osd.exceptions import CapabilitySetNotFoundError, CycleNotFoundError
from ska_ost_osd.osd.models.capabilities import (
    CapabilitySet,
    LowBasicCapabilities,
    LowCapabilitySet,
    MidBasicCapabilities,
    MidCapabilitySet,
)
from ska_ost_osd.osd.models.constraints import Constraints
from ska_ost_osd.osd.models.cycles import Cycle, CycleID
from ska_ost_osd.osd.models.defaults import LowDefaults, MidDefaults
from ska_ost_osd.osd.models.subarray_templates import SubarrayTemplate

_CAPABILITY_SET_MODELS = {
    Telescope.SKA_MID: MidCapabilitySet,
    Telescope.SKA_LOW: LowCapabilitySet,
}

_DEFAULTS_MODELS = {
    Telescope.SKA_MID: MidDefaults,
    Telescope.SKA_LOW: LowDefaults,
}

# The fields of a cycle's telescope_capabilities, by telescope
_CYCLE_TELESCOPE_FIELDS = {
    Telescope.SKA_MID: "ska_mid",
    Telescope.SKA_LOW: "ska_low",
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
        return storage.get_cycle_ids(self._tmdata)

    def get_cycle(self, cycle_id: CycleID) -> Cycle:
        cycle_ids = self.get_cycle_ids()
        if cycle_id not in cycle_ids:
            raise CycleNotFoundError(cycle_id, cycle_ids)
        return self._to_cycle(storage.get_cycle_file(self._tmdata, cycle_id))

    def get_cycles(self) -> list[Cycle]:
        return [
            self._to_cycle(storage.get_cycle_file(self._tmdata, cycle_id))
            for cycle_id in self.get_cycle_ids()
        ]

    # Per telescope

    @overload
    def get_defaults(self, telescope: Literal[Telescope.SKA_MID]) -> MidDefaults: ...

    @overload
    def get_defaults(self, telescope: Literal[Telescope.SKA_LOW]) -> LowDefaults: ...

    def get_defaults(self, telescope: Telescope) -> MidDefaults | LowDefaults:
        return _DEFAULTS_MODELS[telescope].model_validate(
            storage.get_telescope_defaults(self._tmdata, telescope),
            from_attributes=True,
        )

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
        return storage.get_telescope_basic_capabilities(self._tmdata, telescope)

    def get_constraints(self, telescope: Telescope) -> Constraints:
        """tmdata stores the constraints in two files: the elevation limits
        in the capabilities file, and the sun, moon and Jupiter avoidance
        angles in the defaults file."""
        capabilities = storage.get_telescope_capabilities(self._tmdata, telescope)
        defaults = storage.get_telescope_defaults(self._tmdata, telescope)
        return Constraints(
            **capabilities.constraints.model_dump(),
            **defaults.constraints.model_dump(),
        )

    # Capability sets

    @overload
    def get_capability_sets(
        self, telescope: Literal[Telescope.SKA_MID]
    ) -> list[MidCapabilitySet]: ...

    @overload
    def get_capability_sets(
        self, telescope: Literal[Telescope.SKA_LOW]
    ) -> list[LowCapabilitySet]: ...

    def get_capability_sets(
        self, telescope: Telescope
    ) -> list[MidCapabilitySet] | list[LowCapabilitySet]:
        return [
            _CAPABILITY_SET_MODELS[telescope].model_validate(
                {
                    "name": name,
                    **capability_set_file.model_dump(exclude={"array_assembly"}),
                }
            )
            for name, capability_set_file in storage.get_capability_set_files(
                self._tmdata, telescope
            ).items()
        ]

    @overload
    def get_capability_set(
        self, telescope: Literal[Telescope.SKA_MID], name: str
    ) -> MidCapabilitySet: ...

    @overload
    def get_capability_set(
        self, telescope: Literal[Telescope.SKA_LOW], name: str
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
        """The capability set's file names the array assembly whose template
        library it offers. A capability set with no array assembly, or an
        array assembly with no template library, offers none."""
        capability_set_files = storage.get_capability_set_files(self._tmdata, telescope)
        if capability_set not in capability_set_files:
            raise CapabilitySetNotFoundError(
                telescope, capability_set, list(capability_set_files)
            )
        array_assembly = capability_set_files[capability_set].array_assembly
        if array_assembly is None:
            return []
        try:
            library = storage.get_subarray_template_library(
                self._tmdata, telescope, array_assembly
            )
        except FileNotFoundError:
            return []
        return library.templates

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
