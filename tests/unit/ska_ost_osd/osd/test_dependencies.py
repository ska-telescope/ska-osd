from ska_ost_osd.osd.models.models import OSDQueryParams
from ska_ost_osd.osd.routers.dependencies import (
    get_tmdata_for_osd_query,
    get_tmdata_gitlab_main,
)


def test_get_tmdata_for_osd_query_maps_cycle_1_to_first_tag(tests_tmdata):
    """Cycle 1 should resolve to the first version in version mapping."""
    osd_model = OSDQueryParams(cycle_id=1, source="car")
    tm_data = get_tmdata_for_osd_query(osd_model, tests_tmdata)
    assert tm_data.get_sources() == ["car:ost/ska-ost-osd?4.2.1"]


def test_get_tmdata_for_osd_query_maps_cycle_10000_to_first_tag(tests_tmdata):
    """Cycle 10000 should resolve to the first version in version mapping."""
    osd_model = OSDQueryParams(cycle_id=10000, source="car")
    tm_data = get_tmdata_for_osd_query(osd_model, tests_tmdata)
    assert tm_data.get_sources() == ["car:ost/ska-ost-osd?5.1.0"]


def test_get_tmdata_gitlab_main_uses_gitlab_main_source():
    """GitLab main dependency should construct TMData with expected source."""
    tm_data = get_tmdata_gitlab_main()
    assert tm_data.get_sources() == [
        "gitlab://gitlab.com/ska-telescope/ost/ska-ost-osd?main#tmdata"
    ]
