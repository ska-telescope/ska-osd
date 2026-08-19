"""Router dependencies.

FastAPI dependencies for the OSD routers, including TMData clients.
"""

from fastapi import Depends
from ska_telmodel_client import TMData

from ska_ost_osd.osd.common.constant import BASE_FOLDER_NAME, CAR_URL
from ska_ost_osd.osd.models.models import OSDQueryParams
from ska_ost_osd.osd.osd import build_tmdata_for_osd_query


def get_tmdata_car_main():
    return TMData([f"car:{CAR_URL}main#{BASE_FOLDER_NAME}"], update=True)


def get_tmdata_for_osd_query(
    osd_model: OSDQueryParams = Depends(),
) -> TMData:
    """Resolve TMData for /osd queries from query parameters."""
    return build_tmdata_for_osd_query(
        cycle_id=osd_model.cycle_id,
        osd_version=osd_model.osd_version,
        source=osd_model.source,
        gitlab_branch=osd_model.gitlab_branch,
        capabilities=osd_model.capabilities,
        array_assembly=osd_model.array_assembly,
    )


def get_osd_query_context(
    osd_model: OSDQueryParams = Depends(),
) -> tuple[OSDQueryParams, TMData]:
    """Provide validated query model and resolved TMData for /osd."""
    tm_data = get_tmdata_for_osd_query(osd_model)
    return osd_model, tm_data
