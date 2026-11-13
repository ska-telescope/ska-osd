"""The OSD repository backed by the tmdata, read through a TMData client."""

from typing import Literal, overload

from ska_telmodel_client import TMData

from ska_ost_osd.osd.adapters.tmdata import storage
from ska_ost_osd.osd.adapters.tmdata.models import CycleFile, MidDefaultsFile
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
from ska_ost_osd.osd.models.cycles import Cycle, PolicyType
from ska_ost_osd.osd.models.defaults import LowDefaults, MidDefaults, SPFRxParameters
from ska_ost_osd.osd.models.subarray_templates import SubarrayTemplate

_CAPABILITY_SET_MODELS = {
    Telescope.SKA_MID: MidCapabilitySet,
    Telescope.SKA_LOW: LowCapabilitySet,
}


class TMDataRepository:
    """Implements ``OSDRepository`` by reading the tmdata through a TMData
    client.

    :param tmdata: the TMData client to read from.
    """

    def __init__(self, tmdata: TMData):
        self._tmdata = tmdata

    # Cycles

    def get_cycle_ids(self) -> list[str]:
        return storage.get_cycle_ids(self._tmdata)

    def get_cycle(self, cycle_id: str) -> Cycle:
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
        defaults = storage.get_telescope_defaults(self._tmdata, telescope)
        if isinstance(defaults, MidDefaultsFile):
            return MidDefaults(
                spfrx_defaults=SPFRxParameters(
                    target_spfrx=defaults.target.dish_spfrx_params,
                    csp_spfrx=defaults.csp_configuration.spfrx,
                )
            )
        return LowDefaults(quality_attribute_metrics=defaults.quality_attribute_metrics)

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
        in the basic capabilities file, and the sun, moon and Jupiter
        avoidance angles in the defaults file."""
        basic_capabilities = storage.get_telescope_basic_capabilities(
            self._tmdata, telescope
        )
        defaults = storage.get_telescope_defaults(self._tmdata, telescope)
        return Constraints(
            **basic_capabilities.elevation_limits.model_dump(),
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
                    **array_assembly_file.model_dump(exclude={"array_assembly"}),
                }
            )
            for name, array_assembly_file in storage.get_array_assembly_files(
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
        array_assembly_files = storage.get_array_assembly_files(self._tmdata, telescope)
        if capability_set not in array_assembly_files:
            raise CapabilitySetNotFoundError(
                telescope, capability_set, list(array_assembly_files)
            )
        array_assembly = array_assembly_files[capability_set].array_assembly
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
        self, cycle_id: str
    ) -> dict[Telescope, dict[PolicyType, CapabilitySet]]:
        return {
            telescope: {
                policy_type: self.get_capability_set(telescope, name)
                for policy_type, name in offered.policies.items()
            }
            for telescope, offered in self.get_cycle(cycle_id).capabilities.items()
        }

    # Storage to reader models

    @staticmethod
    def _to_cycle(cycle_file: CycleFile) -> Cycle:
        return Cycle.model_validate(cycle_file, from_attributes=True)
