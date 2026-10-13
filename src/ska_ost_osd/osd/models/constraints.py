from typing import Self

from ska_ost_osd.osd.models.capabilities import (
    ElevationConstraints,
    TelescopeCapabilitiesFileBase,
)
from ska_ost_osd.osd.models.defaults import (
    AvoidanceConstraints,
    TelescopeDefaultsFileBase,
)


class Constraints(ElevationConstraints, AvoidanceConstraints):
    """A telescope's observing constraints, which tmdata stores in two
    files."""

    @classmethod
    def combine(
        cls,
        capabilities: TelescopeCapabilitiesFileBase,
        defaults: TelescopeDefaultsFileBase,
    ) -> Self:
        """The elevation limits from the capabilities file with the sun,
        moon and Jupiter avoidance angles from the defaults file."""
        return cls(
            **capabilities.constraints.model_dump(),
            **defaults.constraints.model_dump(),
        )
