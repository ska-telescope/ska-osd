"""Functions that read the OSD tmdata and return it as pydantic models.

Each function takes the TMData to read from, so the caller chooses the
source and version and handles any caching.
"""

from ska_telmodel_client import TMData

from ska_ost_osd.osd.common.constant import OBSERVING_CYCLES_TMDATA_DIR
from ska_ost_osd.osd.exceptions import CycleNotFoundError
from ska_ost_osd.osd.models.observatory_policies import CycleID, ObservatoryPolicy


def get_cycle_ids(tmdata: TMData) -> list[CycleID]:
    """List the cycle IDs, from the ``cycles/cycle_<N>.json`` file names.

    :param tmdata: TMData to read from.
    :return: the cycle IDs in ascending order.
    :raises FileNotFoundError: If the tmdata has no cycles directory.
    """
    if not any(key.startswith(OBSERVING_CYCLES_TMDATA_DIR) for key in tmdata):
        raise FileNotFoundError(f"file not found: {OBSERVING_CYCLES_TMDATA_DIR}")
    return sorted(
        CycleID(int(key.removeprefix("cycle_").removesuffix(".json")))
        for key in tmdata[OBSERVING_CYCLES_TMDATA_DIR]
        if key.startswith("cycle_") and key.endswith(".json")
    )


def get_cycle(tmdata: TMData, cycle_id: CycleID) -> ObservatoryPolicy:
    """Read one cycle, from ``cycles/cycle_<N>.json``: its metadata,
    policies and the capability set each telescope offers.

    :param tmdata: TMData to read from.
    :param cycle_id: the ID of the cycle.
    :return: the cycle.
    :raises CycleNotFoundError: If there is no cycle with that ID.
    :raises FileNotFoundError: If the tmdata has no cycles directory.
    """
    cycle_ids = get_cycle_ids(tmdata)
    if cycle_id not in cycle_ids:
        raise CycleNotFoundError(cycle_id, cycle_ids)
    return ObservatoryPolicy.model_validate(
        tmdata[f"{OBSERVING_CYCLES_TMDATA_DIR}/cycle_{cycle_id}.json"].get_dict()
    )
