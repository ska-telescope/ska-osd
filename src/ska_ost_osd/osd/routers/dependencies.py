"""Router dependencies.

FastAPI dependencies for the OSD routers, including TMData clients.
"""

from ska_telmodel_client import TMData

from ska_ost_osd.osd.common.constant import (
    BASE_FOLDER_NAME,
    BASE_URL,
    CAR_URL,
)


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
