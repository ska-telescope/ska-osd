"""Router dependencies.

FastAPI dependencies for the OSD routers, including TMData clients.
"""

from fastapi import Depends
from ska_telmodel_client import TMData

from ska_ost_osd.osd.common.constant import (
    BASE_FOLDER_NAME,
    BASE_URL,
    CAR_URL,
    VERSION_FILE_PATH,
)
from ska_ost_osd.osd.common.error_handling import OSDModelError
from ska_ost_osd.osd.models.models import OSDModel, OSDQueryParams
from ska_ost_osd.osd.osd import osd_tmdata_source


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
    errors = []

    try:
        OSDModel(
            source=osd_model.source,
            cycle_id=osd_model.cycle_id,
            osd_version=osd_model.osd_version,
            capabilities=osd_model.capabilities,
            array_assembly=osd_model.array_assembly,
        )
    except OSDModelError as error:
        errors.extend(error.args[0])

    versions_dict = tmdata[VERSION_FILE_PATH].get_dict()
    source_uris, source_errors = osd_tmdata_source(
        cycle_id=osd_model.cycle_id,
        osd_version=osd_model.osd_version,
        source=osd_model.source,
        gitlab_branch=osd_model.gitlab_branch,
        versions_dict=versions_dict,
        tmdata=tmdata,
    )

    if source_errors:
        errors.extend(source_errors)

    if errors:
        raise ValueError(errors)

    return TMData(source_uris=source_uris)
