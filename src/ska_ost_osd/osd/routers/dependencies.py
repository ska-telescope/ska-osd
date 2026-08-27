"""Router dependencies.

FastAPI dependencies for the OSD routers, including TMData clients.
"""

from fastapi import Depends
from ska_telmodel_client import TMData

from ska_ost_osd.osd.common.constant import (
    BASE_FOLDER_NAME,
    BASE_URL,
    CAR_URL,
    SOURCES,
    VERSION_FILE_PATH,
)
from ska_ost_osd.osd.common.error_handling import OSDModelError
from ska_ost_osd.osd.common.osd_validation_messages import (
    AVAILABLE_SOURCE_ERROR_MESSAGE,
    SOURCE_ERROR_MESSAGE,
)
from ska_ost_osd.osd.models.models import OSDModel, OSDQueryParams
from ska_ost_osd.osd.osd import check_cycle_id


def get_tmdata_car_main() -> TMData:
    """Construct a TMData client for the CAR main branch.

    :returns: TMData client for CAR main branch
    """
    return TMData([f"car:{CAR_URL}main#{BASE_FOLDER_NAME}"], update=True)


def get_tmdata_gitlab_main() -> TMData:
    """Construct a TMData client for the GitLab main branch.

    :returns: TMData client for GitLab main branch
    """
    return TMData(
        [f"gitlab:{BASE_URL}{CAR_URL}main#{BASE_FOLDER_NAME}"],
        update=True,
    )


def get_tmdata_for_osd_query(
    osd_model: OSDQueryParams = Depends(),
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
    source = osd_model.source

    if source not in SOURCES:
        source_msg = ", ".join(SOURCES)
        errors.append(AVAILABLE_SOURCE_ERROR_MESSAGE.format(source_msg))

    if (
        osd_model.gitlab_branch
        and isinstance(osd_model.gitlab_branch, str)
        and source in ("car", "file")
    ):
        errors.append(SOURCE_ERROR_MESSAGE.format(source))

    osd_version, cycle_errors = check_cycle_id(
        tmdata=tmdata,
        cycle_id=osd_model.cycle_id,
        osd_version=osd_model.osd_version,
        gitlab_branch=osd_model.gitlab_branch,
        versions_dict=versions_dict,
    )
    if cycle_errors:
        errors.extend(cycle_errors)

    if errors:
        raise ValueError(errors)

    source_uris = (f"{source}:{BASE_URL}{CAR_URL}{osd_version}#{BASE_FOLDER_NAME}",)
    if source == "file":
        source_uris = (f"{source}://{BASE_FOLDER_NAME}",)
    if source == "car":
        source_uris = (f"{source}:{CAR_URL}{osd_version}#{BASE_FOLDER_NAME}",)

    return TMData(source_uris=source_uris)
