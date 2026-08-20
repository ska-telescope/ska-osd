from unittest.mock import Mock

from ska_ost_osd.osd.models.models import OSDQueryParams
from ska_ost_osd.osd.routers.dependencies import (
    get_tmdata_for_osd_query,
    get_tmdata_gitlab_main,
)
from tests import conftest as test_conftest


def test_get_osd_query_context_maps_cycle_1_to_first_tag(monkeypatch, tests_tmdata):
    """Cycle 1 should resolve to the first version in version mapping."""
    monkeypatch.setattr(
        "ska_ost_osd.osd.routers.dependencies.osd_tmdata_source",
        test_conftest.osd_tmdata_source,
    )
    tmdata_constructor = Mock(side_effect=lambda *args, **kwargs: tests_tmdata)
    monkeypatch.setattr(
        "ska_ost_osd.osd.routers.dependencies.TMData", tmdata_constructor
    )

    osd_model = OSDQueryParams(cycle_id=1, source="car")
    tm_data = get_tmdata_for_osd_query(osd_model, tests_tmdata)
    assert tm_data is tests_tmdata
    assert tmdata_constructor.call_count == 1
    assert tmdata_constructor.call_args.kwargs["source_uris"] == (
        "car:ost/ska-ost-osd?4.2.1#tmdata",
    )


def test_get_osd_query_context_maps_cycle_10000_to_first_tag(monkeypatch, tests_tmdata):
    """Cycle 10000 should resolve to the first version in version mapping."""
    monkeypatch.setattr(
        "ska_ost_osd.osd.routers.dependencies.osd_tmdata_source",
        test_conftest.osd_tmdata_source,
    )
    tmdata_constructor = Mock(side_effect=lambda *args, **kwargs: tests_tmdata)
    monkeypatch.setattr(
        "ska_ost_osd.osd.routers.dependencies.TMData", tmdata_constructor
    )

    osd_model = OSDQueryParams(cycle_id=10000, source="car")
    tm_data = get_tmdata_for_osd_query(osd_model, tests_tmdata)
    assert tm_data is tests_tmdata
    assert tmdata_constructor.call_count == 1
    assert tmdata_constructor.call_args.kwargs["source_uris"] == (
        "car:ost/ska-ost-osd?5.1.0#tmdata",
    )


def test_get_tmdata_gitlab_main_uses_gitlab_main_source(monkeypatch, tests_tmdata):
    """GitLab main dependency should construct TMData with expected source."""
    tmdata_constructor = Mock(return_value=tests_tmdata)
    monkeypatch.setattr(
        "ska_ost_osd.osd.routers.dependencies.TMData",
        tmdata_constructor,
    )
    tm_data = get_tmdata_gitlab_main()

    assert tm_data is tests_tmdata
    assert tmdata_constructor.call_args.args[0] == [
        "gitlab://gitlab.com/ska-telescope/ost/ska-ost-osd?main#tmdata"
    ]
