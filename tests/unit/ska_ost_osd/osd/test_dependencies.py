import pytest

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


@pytest.mark.parametrize(
    "cycle_id, source, capabilities",
    [
        (3, "file", "mid"),
        (2, "file", "low"),
    ],
)
def test_get_tmdata_for_osd_query_rejects_invalid_cycle_ids(
    tests_tmdata,
    cycle_id,
    source,
    capabilities,
):
    """Invalid cycle IDs should raise from dependency resolution."""
    osd_model = OSDQueryParams(
        cycle_id=cycle_id,
        source=source,
        capabilities=capabilities,
    )

    with pytest.raises(ValueError) as error:
        get_tmdata_for_osd_query(osd_model=osd_model, tmdata=tests_tmdata)
    assert f"Cycle {cycle_id} is not valid" in error.value.args[0][0]


def test_get_tmdata_for_osd_query_reports_combined_validation_errors(tests_tmdata):
    """Dependency should surface combined model and cycle validation errors."""
    osd_model = OSDQueryParams(
        cycle_id=100000,
        osd_version="1..1.0",
        source="file",
        capabilities="mid",
        array_assembly="AAA3",
    )

    with pytest.raises(ValueError) as error:
        get_tmdata_for_osd_query(osd_model=osd_model, tmdata=tests_tmdata)

    assert error.value.args[0] == [
        "Cycle_id and Array_assembly cannot be used together",
        "osd_version 1..1.0 is not valid",
        "array_assembly AAA3 is not valid",
        "Cycle 100000 is not valid,Available IDs are 1,10000",
    ]


def test_get_tmdata_for_osd_query_requires_cycle_or_capabilities(tests_tmdata):
    """Dependency should reject empty OSD query inputs."""
    osd_model = OSDQueryParams()

    with pytest.raises(ValueError) as error:
        get_tmdata_for_osd_query(osd_model=osd_model, tmdata=tests_tmdata)

    assert error.value.args[0] == ["Either cycle_id or capabilities must be provided"]
