"""The OSD repository backed by the tmdata, read through a TMData client."""

from typing import Any, Literal, overload

from ska_telmodel_client import TMData

from ska_ost_osd.osd.adapters.tmdata import storage
from ska_ost_osd.osd.adapters.tmdata.models import CycleFile, MidDefaultsFile
from ska_ost_osd.osd.common.constant import Telescope
from ska_ost_osd.osd.exceptions import ArrayAssemblyNotFoundError, CycleNotFoundError
from ska_ost_osd.osd.models.capabilities import (
    Capabilities,
    LowBasicCapabilities,
    LowCapabilities,
    MidBasicCapabilities,
    MidCapabilities,
)
from ska_ost_osd.osd.models.constraints import Constraints
from ska_ost_osd.osd.models.cycles import Cycle, PolicyType
from ska_ost_osd.osd.models.defaults import LowDefaults, MidDefaults, SPFRxParameters
from ska_ost_osd.osd.models.subarray_templates import SubarrayTemplate

_CAPABILITIES_MODELS = {
    Telescope.SKA_MID: MidCapabilities,
    Telescope.SKA_LOW: LowCapabilities,
}


def merge_capabilities(
    capabilities: dict[str, Any], policy: dict[str, Any]
) -> dict[str, Any]:
    """The capabilities with each field the policy sets replaced, nested
    groups field by field."""
    merged = dict(capabilities)
    for field, value in policy.items():
        merged[field] = (
            merge_capabilities(capabilities[field], value)
            if isinstance(value, dict)
            else value
        )
    return merged


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
        return [
            _CAPABILITIES_MODELS[telescope].model_validate(
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
        array_assembly_files = storage.get_array_assembly_files(self._tmdata, telescope)
        if array_assembly not in array_assembly_files:
            raise ArrayAssemblyNotFoundError(
                telescope, array_assembly, list(array_assembly_files)
            )
        capabilities = array_assembly_files[array_assembly].model_dump(
            exclude={"array_assembly"}
        )
        if policy_id is not None:
            policy = storage.get_policy_file(self._tmdata, telescope, policy_id)
            capabilities = merge_capabilities(
                capabilities, policy.model_dump(exclude={"id"}, exclude_unset=True)
            )
        return _CAPABILITIES_MODELS[telescope].model_validate(
            {"name": policy_id or array_assembly, **capabilities}
        )

    # Joins

    def get_subarray_templates(
        self, telescope: Telescope, array_assembly: str
    ) -> list[SubarrayTemplate]:
        """The array assembly's file names the template library it offers. An
        array assembly with none named, or whose library doesn't exist,
        offers none."""
        array_assembly_files = storage.get_array_assembly_files(self._tmdata, telescope)
        if array_assembly not in array_assembly_files:
            raise ArrayAssemblyNotFoundError(
                telescope, array_assembly, list(array_assembly_files)
            )
        library_name = array_assembly_files[array_assembly].array_assembly
        if library_name is None:
            return []
        try:
            library = storage.get_subarray_template_library(
                self._tmdata, telescope, library_name
            )
        except FileNotFoundError:
            return []
        return library.templates

    def get_cycle_capabilities(
        self, cycle_id: str
    ) -> dict[Telescope, dict[PolicyType, Capabilities]]:
        return {
            telescope: {
                policy_type: self.get_capabilities(
                    telescope, offered.array_assembly, policy_id
                )
                for policy_type, policy_id in offered.policies.items()
            }
            for telescope, offered in self.get_cycle(cycle_id).capabilities.items()
        }

    # Storage to reader models

    @staticmethod
    def _to_cycle(cycle_file: CycleFile) -> Cycle:
        return Cycle.model_validate(cycle_file, from_attributes=True)
