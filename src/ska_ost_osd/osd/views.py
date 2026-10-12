"""Views: the query results recast into the shapes their consumers use.

Views build only on the functions in ``ska_ost_osd.osd.queries`` and never
read the tmdata themselves.
"""

from ska_telmodel_client import TMData

from ska_ost_osd.osd.common.constant import Telescope
from ska_ost_osd.osd.models.configuration import (
    Configuration,
    ConfigurationLowQualityAttributeMetrics,
    CycleCapabilities,
    CycleConfiguration,
    LowConfiguration,
    LowConfigurationCapabilitySet,
    LowCycleCapabilities,
    MidConfiguration,
    MidConfigurationCapabilitySet,
    MidCycleCapabilities,
)
from ska_ost_osd.osd.models.cycles import CycleID
from ska_ost_osd.osd.queries import (
    get_basic_capabilities,
    get_capability_sets,
    get_constraints,
    get_cycle,
    get_cycle_capability_sets,
    get_cycle_ids,
    get_defaults,
)


def get_configuration(tmdata: TMData) -> Configuration:
    """Build the ODT configuration: what ska-oso-services serves from GET
    /configuration.

    :param tmdata: TMData to read from.
    :return: both telescopes' bands, constraints, defaults and capability
        sets.
    :raises FileNotFoundError: If the tmdata has no capabilities or defaults
        file for a telescope.
    """
    return Configuration(
        ska_mid=MidConfiguration(
            frequency_band=get_basic_capabilities(
                tmdata, Telescope.MID
            ).frequency_bands,
            constraints=get_constraints(tmdata, Telescope.MID),
            subarrays=[
                MidConfigurationCapabilitySet.model_validate(
                    capability_set, from_attributes=True
                )
                for capability_set in get_capability_sets(tmdata, Telescope.MID)
            ],
            spfrx_defaults=get_defaults(tmdata, Telescope.MID).spfrx_defaults,
        ),
        ska_low=LowConfiguration(
            frequency_band=get_basic_capabilities(tmdata, Telescope.LOW),
            constraints=get_constraints(tmdata, Telescope.LOW),
            quality_attribute_metrics=ConfigurationLowQualityAttributeMetrics.model_validate(
                get_defaults(tmdata, Telescope.LOW).quality_attribute_metrics,
                from_attributes=True,
            ),
            subarrays=[
                LowConfigurationCapabilitySet.model_validate(
                    capability_set, from_attributes=True
                )
                for capability_set in get_capability_sets(tmdata, Telescope.LOW)
            ],
        ),
    )


def get_cycle_configuration(tmdata: TMData, cycle_id: CycleID) -> CycleConfiguration:
    """Build one cycle's view for the PHT: what ska-oso-services serves from
    GET /prsls/osd/{cycle}.

    :param tmdata: TMData to read from.
    :param cycle_id: the ID of the cycle.
    :return: the cycle with, for each telescope it offers, the offered
        capability set and that telescope's basic capabilities.
    :raises CycleNotFoundError: If there is no cycle with that ID.
    :raises CapabilitySetNotFoundError: If the cycle names a capability set
        that does not exist.
    :raises FileNotFoundError: If a tmdata file is missing.
    """
    capability_sets = get_cycle_capability_sets(tmdata, cycle_id)
    mid = capability_sets.get(Telescope.MID)
    low = capability_sets.get(Telescope.LOW)
    return CycleConfiguration(
        observatory_policy=get_cycle(tmdata, cycle_id),
        capabilities=CycleCapabilities(
            mid=MidCycleCapabilities(
                basic_capabilities=get_basic_capabilities(tmdata, Telescope.MID),
                capability_set=mid,
            )
            if mid
            else None,
            low=LowCycleCapabilities(
                basic_capabilities=get_basic_capabilities(tmdata, Telescope.LOW),
                capability_set=low,
            )
            if low
            else None,
        ),
    )


def get_cycle_configurations(tmdata: TMData) -> list[CycleConfiguration]:
    """Build every cycle's view for the PHT, in ascending order of ID: what
    ska-oso-services serves from GET /prsls/osd/cycles.

    :param tmdata: TMData to read from.
    :return: the cycle views.
    :raises CapabilitySetNotFoundError: If a cycle names a capability set
        that does not exist.
    :raises FileNotFoundError: If a tmdata file is missing.
    """
    return [
        get_cycle_configuration(tmdata, cycle_id) for cycle_id in get_cycle_ids(tmdata)
    ]
