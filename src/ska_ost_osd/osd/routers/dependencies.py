"""Router dependencies.

FastAPI dependencies for the OSD routers, including TMData clients.
"""

from fastapi import Depends
from ska_telmodel_client import TMData

from ska_ost_osd.osd import osd as osd_service
from ska_ost_osd.osd.common.constant import BASE_FOLDER_NAME, BASE_URL, CAR_URL
from ska_ost_osd.osd.models.models import OSDQueryParams


def get_tmdata_car_main():
    return TMData([f"car:{CAR_URL}main#{BASE_FOLDER_NAME}"], update=True)


def get_tmdata_gitlab_main():
    return TMData(
        [f"gitlab:{BASE_URL}{CAR_URL}main#{BASE_FOLDER_NAME}"],
        update=True,
    )


def get_osd_query_model(
    osd_model: OSDQueryParams = Depends(),
) -> OSDQueryParams:
    """Provide validated OSD query model."""
    return osd_model


def get_tmdata_for_osd_query(
    osd_model: OSDQueryParams = Depends(get_osd_query_model),
    tmdata: TMData = Depends(get_tmdata_gitlab_main),
) -> TMData:
    """Resolve TMData for /osd from the query model."""
    return osd_service.build_tmdata_for_osd_query(
        tmdata=tmdata,
        cycle_id=osd_model.cycle_id,
        osd_version=osd_model.osd_version,
        source=osd_model.source,
        gitlab_branch=osd_model.gitlab_branch,
        capabilities=osd_model.capabilities,
        array_assembly=osd_model.array_assembly,
    )
