from ska_ost_osd.osd.models.capabilities import ElevationConstraints
from ska_ost_osd.osd.models.defaults import AvoidanceConstraints


class Constraints(ElevationConstraints, AvoidanceConstraints):
    """A telescope's observing constraints: its elevation limits and its
    sun, moon and Jupiter avoidance angles."""
