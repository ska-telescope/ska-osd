"""Views: the repository's data recast into the shapes its consumers use.

Views build only on the methods of ``OSDRepository``, so they work with any
repository; errors from reading the data come from the repository.
"""

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
from ska_ost_osd.osd.repository import OSDRepository


def get_configuration(repository: OSDRepository) -> Configuration:
    """Build the ODT configuration: what ska-oso-services serves from GET
    /configuration.

    :param repository: the OSD repository to read from.
    :return: both telescopes' bands, constraints, defaults and capability
        sets.
    """
    return Configuration(
        ska_mid=MidConfiguration(
            frequency_band=repository.get_basic_capabilities(
                Telescope.MID
            ).frequency_bands,
            constraints=repository.get_constraints(Telescope.MID),
            subarrays=[
                MidConfigurationCapabilitySet.model_validate(
                    capability_set, from_attributes=True
                )
                for capability_set in repository.get_capability_sets(Telescope.MID)
            ],
            spfrx_defaults=repository.get_defaults(Telescope.MID).spfrx_defaults,
        ),
        ska_low=LowConfiguration(
            frequency_band=repository.get_basic_capabilities(Telescope.LOW),
            constraints=repository.get_constraints(Telescope.LOW),
            quality_attribute_metrics=ConfigurationLowQualityAttributeMetrics.model_validate(
                repository.get_defaults(Telescope.LOW).quality_attribute_metrics,
                from_attributes=True,
            ),
            subarrays=[
                LowConfigurationCapabilitySet.model_validate(
                    capability_set, from_attributes=True
                )
                for capability_set in repository.get_capability_sets(Telescope.LOW)
            ],
        ),
    )


def get_cycle_configuration(
    repository: OSDRepository, cycle_id: CycleID
) -> CycleConfiguration:
    """Build one cycle's view for the PHT: what ska-oso-services serves from
    GET /prsls/osd/{cycle}.

    :param repository: the OSD repository to read from.
    :param cycle_id: the ID of the cycle.
    :return: the cycle with, for each telescope it offers, the offered
        capability set and that telescope's basic capabilities.
    :raises CycleNotFoundError: If there is no cycle with that ID.
    :raises CapabilitySetNotFoundError: If the cycle names a capability set
        that does not exist.
    """
    capability_sets = repository.get_cycle_capability_sets(cycle_id)
    mid = capability_sets.get(Telescope.MID)
    low = capability_sets.get(Telescope.LOW)
    return CycleConfiguration(
        observatory_policy=repository.get_cycle(cycle_id),
        capabilities=CycleCapabilities(
            mid=MidCycleCapabilities(
                basic_capabilities=repository.get_basic_capabilities(Telescope.MID),
                capability_set=mid,
            )
            if mid
            else None,
            low=LowCycleCapabilities(
                basic_capabilities=repository.get_basic_capabilities(Telescope.LOW),
                capability_set=low,
            )
            if low
            else None,
        ),
    )


def get_cycle_configurations(repository: OSDRepository) -> list[CycleConfiguration]:
    """Build every cycle's view for the PHT, in ascending order of ID: what
    ska-oso-services serves from GET /prsls/osd/cycles.

    :param repository: the OSD repository to read from.
    :return: the cycle views.
    :raises CapabilitySetNotFoundError: If a cycle names a capability set
        that does not exist.
    """
    return [
        get_cycle_configuration(repository, cycle_id)
        for cycle_id in repository.get_cycle_ids()
    ]
