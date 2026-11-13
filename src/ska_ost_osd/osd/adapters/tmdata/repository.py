"""The OSD repository backed by the tmdata, read through a TMData client."""

from typing import Literal, overload

from ska_telmodel_client import TMData

from ska_ost_osd.osd.adapters.tmdata import storage
from ska_ost_osd.osd.adapters.tmdata.models import CycleFile, MidDefaultsFile
from ska_ost_osd.osd.common.constant import Telescope
from ska_ost_osd.osd.exceptions import (
    ArrayAssemblyNotFoundError,
    CycleNotFoundError,
    PolicyNotFoundError,
)
from ska_ost_osd.osd.models.capabilities import (
    Capabilities,
    LowBasicCapabilities,
    LowCapabilities,
    MidBasicCapabilities,
    MidCapabilities,
    merge_capabilities,
)
from ska_ost_osd.osd.models.constraints import Constraints
from ska_ost_osd.osd.models.cycles import Cycle, PolicyType
from ska_ost_osd.osd.models.defaults import LowDefaults, MidDefaults, SPFRxParameters
from ska_ost_osd.osd.models.subarray_templates import SubarrayTemplate

_CAPABILITIES_MODELS = {
    Telescope.SKA_MID: MidCapabilities,
    Telescope.SKA_LOW: LowCapabilities,
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

    # Capabilities

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
            self.get_capabilities(telescope, name)
            for name in storage.get_array_assembly_files(self._tmdata, telescope)
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
        policy = None
        if policy_id is not None:
            try:
                policy_ids = list(storage.get_policy_paths(self._tmdata, telescope))
            except FileNotFoundError:
                policy_ids = []
            if policy_id not in policy_ids:
                raise PolicyNotFoundError(telescope, policy_id, policy_ids)
            policy = storage.get_policy_file(
                self._tmdata, telescope, policy_id
            ).model_dump(exclude_unset=True)
        return _CAPABILITIES_MODELS[telescope].model_validate(
            merge_capabilities(
                storage.get_telescope_basic_capabilities(
                    self._tmdata, telescope
                ).model_dump(),
                array_assembly_files[array_assembly].model_dump(),
                policy,
            )
        )

    # Joins

    def get_subarray_templates(
        self, telescope: Telescope, array_assembly: str
    ) -> list[SubarrayTemplate]:
        """An array assembly's templates are the library of the same name; one
        with no library offers none."""
        array_assembly_files = storage.get_array_assembly_files(self._tmdata, telescope)
        if array_assembly not in array_assembly_files:
            raise ArrayAssemblyNotFoundError(
                telescope, array_assembly, list(array_assembly_files)
            )
        try:
            library = storage.get_subarray_template_library(
                self._tmdata, telescope, array_assembly
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
