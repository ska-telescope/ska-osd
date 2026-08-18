"""Router dependencies.

FastAPI dependencies for the OSD routers, including TMData clients.
"""

from ska_telmodel_client import TMData

from ska_ost_osd.osd.common.constant import BASE_FOLDER_NAME, CAR_URL


def get_tmdata_car_main():
    return TMData([f"car:{CAR_URL}main#{BASE_FOLDER_NAME}"], update=True)
