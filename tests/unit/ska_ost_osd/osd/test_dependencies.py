from unittest.mock import Mock

from ska_ost_osd.osd.models.models import OSDQueryParams
from ska_ost_osd.osd.routers.dependencies import (
    get_osd_query_context,
    get_tmdata_for_osd_query,
)
from tests import conftest as test_conftest


def test_get_tmdata_for_osd_query_maps_cycle_1_to_first_tag(monkeypatch, tests_tmdata):
    """Cycle 1 should resolve to the first version in version mapping."""
    monkeypatch.setattr(
        "ska_ost_osd.osd.osd.osd_tmdata_source",
        test_conftest.osd_tmdata_source,
    )
    tmdata_constructor = Mock(side_effect=lambda *args, **kwargs: tests_tmdata)
    monkeypatch.setattr("ska_ost_osd.osd.osd.TMData", tmdata_constructor)

    osd_model = OSDQueryParams(cycle_id=1, source="car")
    tm_data = get_tmdata_for_osd_query(osd_model)

    assert tm_data is tests_tmdata
    assert tmdata_constructor.call_count == 2
    assert tmdata_constructor.call_args_list[1].kwargs["source_uris"] == (
        "car:ost/ska-ost-osd?4.2.1#tmdata",
    )


def test_get_tmdata_for_osd_query_maps_cycle_10000_to_first_tag(
    monkeypatch, tests_tmdata
):
    """Cycle 10000 should resolve to the first version in version mapping."""
    monkeypatch.setattr(
        "ska_ost_osd.osd.osd.osd_tmdata_source",
        test_conftest.osd_tmdata_source,
    )
    tmdata_constructor = Mock(side_effect=lambda *args, **kwargs: tests_tmdata)
    monkeypatch.setattr("ska_ost_osd.osd.osd.TMData", tmdata_constructor)

    osd_model = OSDQueryParams(cycle_id=10000, source="car")
    tm_data = get_tmdata_for_osd_query(osd_model)

    assert tm_data is tests_tmdata
    assert tmdata_constructor.call_count == 2
    assert tmdata_constructor.call_args_list[1].kwargs["source_uris"] == (
        "car:ost/ska-ost-osd?5.1.0#tmdata",
    )


def test_get_osd_query_context_returns_model_and_tmdata(monkeypatch, tests_tmdata):
    """Context dependency should return the validated model and TMData."""
    monkeypatch.setattr(
        "ska_ost_osd.osd.routers.dependencies.get_tmdata_for_osd_query",
        lambda osd_model: tests_tmdata,
    )
    osd_model = OSDQueryParams(cycle_id=1, source="car", capabilities="mid")

    model, tm_data = get_osd_query_context(osd_model)

    assert model == osd_model
    assert tm_data is tests_tmdata
