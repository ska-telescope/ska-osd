"""Unit tests for the errors the OSD repository raises."""

import pytest

from ska_ost_osd.osd.common.constant import Telescope
from ska_ost_osd.osd.exceptions import (
    ArrayAssemblyNotFoundError,
    Band5bSubbandNotFoundError,
    CycleNotFoundError,
    FrequencyBandNotFoundError,
    OSDQueryError,
    PolicyNotFoundError,
)


@pytest.mark.parametrize(
    "error",
    [
        CycleNotFoundError(
            "NO_SUCH_CYCLE",
            ["TEST_SKAO_2027_Low_AA1_SV", "TEST_SKAO_2027_AA2_Proposal"],
        ),
        ArrayAssemblyNotFoundError(Telescope.SKA_LOW, "AA3", ["AA1", "AA2"]),
        PolicyNotFoundError(Telescope.SKA_LOW, "AA3", ["AA1", "AA2"]),
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
