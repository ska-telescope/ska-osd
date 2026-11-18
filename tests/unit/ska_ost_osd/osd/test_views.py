"""Unit tests for the helpers the views share."""

import pytest

from ska_ost_osd.osd.views.base import legacy_zoom_factors


class TestLegacyZoomFactors:
    """The pre-8.0 responses served Low's zoom factors as the multipliers
    2**z, with 1 for no zoom, or [0] when no zoom is offered."""

    @pytest.mark.parametrize(
        "zoom_factors, served",
        [([], [0]), ([1, 2, 3], [1, 2, 4, 8])],
        ids=["no zoom", "zoom"],
    )
    def test_served_as_multipliers(self, zoom_factors, served):
        assert legacy_zoom_factors(zoom_factors) == served
