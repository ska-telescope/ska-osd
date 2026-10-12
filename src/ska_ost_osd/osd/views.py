"""Views: the query results recast into the shapes their consumers use.

Views build only on the functions in ``ska_ost_osd.osd.queries`` and never
read the tmdata themselves.
"""

from ska_telmodel_client import TMData

from ska_ost_osd.osd.common.constant import Telescope
from ska_ost_osd.osd.models.configuration import (
    Configuration,
    ConfigurationLowQualityAttributeMetrics,
    LowConfiguration,
    LowConfigurationCapabilitySet,
    MidConfiguration,
    MidConfigurationCapabilitySet,
)
from ska_ost_osd.osd.queries import (
    get_basic_capabilities,
    get_capability_sets,
    get_constraints,
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
