"""Unit tests for the errors the OSD repository raises."""

import pytest

from ska_ost_osd.osd.common.constant import Telescope
from ska_ost_osd.osd.exceptions import (
    Band5bSubbandNotFoundError,
    CapabilitySetNotFoundError,
    CycleNotFoundError,
    FrequencyBandNotFoundError,
    OSDQueryError,
)
from ska_ost_osd.osd.models.cycles import CycleID


@pytest.mark.parametrize(
    "error",
    [
        CycleNotFoundError(CycleID(3), [CycleID(1), CycleID(2)]),
        CapabilitySetNotFoundError(Telescope.LOW, "AA3", ["AA1", "AA2"]),
        FrequencyBandNotFoundError("Band_9", ["Band_1"]),
        Band5bSubbandNotFoundError("Band_5b", 4, [1, 2, 3]),
    ],
    ids=lambda error: type(error).__name__,
)
def test_not_found_errors_are_query_and_lookup_errors(error):
    """Callers can catch every query error as OSDQueryError, or as the
    built-in LookupError."""
    assert isinstance(error, OSDQueryError)
    assert isinstance(error, LookupError)
