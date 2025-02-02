import copy
import re
from importlib.metadata import version
from typing import Any, Dict, Optional

from ska_telmodel.data import TMData

from ska_ost_osd.osd.constant import ARRAY_ASSEMBLY_PATTERN
from ska_ost_osd.osd.osd_schema_validator import OSDModel, OSDModelError
from ska_ost_osd.osd.osd_validation_messages import (
    ARRAY_ASSEMBLY_DOESNOT_EXIST_ERROR_MESSAGE,
    AVAILABLE_SOURCE_ERROR_MESSAGE,
    CAPABILITY_DOESNOT_EXIST_ERROR_MESSAGE,
    CYCLE_ERROR_MESSAGE,
    CYCLE_ID_ERROR_MESSAGE,
    OSD_VERSION_ERROR_MESSAGE,
    SOURCE_ERROR_MESSAGE,
)
from ska_ost_osd.rest.api.utils import read_file, update_file

from .constant import (
    ARRAY_ASSEMBLY_PATTERN,
    BASE_FOLDER_NAME,
    BASE_URL,
    CAR_URL,
    LOW_CAPABILITIES_JSON_PATH,
    MID_CAPABILITIES_JSON_PATH,
    OBSERVATORY_POLICIES_JSON_PATH,
    SOURCES,
    osd_file_mapping,
    osd_response_template,
)
from .helper import read_json


class OSD:
    """OSD Class for initialing OSD related variables and methods
    including get_telescope_observatory_policies, get_data and get_osd_data
    """

    def __init__(
        self, capabilities: list, array_assembly: str, tmdata: TMData, cycle_id: int
    ) -> None:
        """This is initializer method for Class OSD

        :param capabilities: mid or low
        :param array_assembly: in mid there are
            AA0.5, AA2 and AA1 you can give any one
        :param tmdata: TMData class object
        :param cycle_id: cycle_id

        :returns: None
        """
        self.cycle_id = cycle_id
        self.osd_data = copy.deepcopy(osd_response_template)
        self.capabilities = capabilities
        self.array_assembly = array_assembly
        self.tmdata = tmdata
        self.keys_list = {}

    def check_capabilities(self, capabilities: list = None) -> None:
        """This method checks if a given capability exists or not
            and raises exception

        :param capabilities: mid, low, or basic_capability

        :returns: raises OSDDataException for capabilities
        """

        capabilities_list = list(osd_file_mapping.keys())[:3]

        if capabilities:
            cap_list = [i for i in capabilities if i.lower() not in capabilities_list]

        if (capabilities is not None and isinstance(capabilities, list)) and (cap_list):
            msg = ", ".join(capabilities_list)
            return CAPABILITY_DOESNOT_EXIST_ERROR_MESSAGE.format(cap_list[0], msg)

    def get_telescope_observatory_policies(
        self,
        capabilities: list = None,
        array_assembly: str = None,
    ) -> dict[dict[str, Any]]:
        """This method checks if capabilities or array assembly
            exists or not and gets it from observatory policies file and
            populates the dictionary and returns it

        :param capabilities: mid or low
        :param array_assembly: in mid there are
            AA0.5, AA2 and AA1 you can give any one

        :returns: returns dictionary of osd data and
            dictionary of capabilities and array assembly
        """
        self.osd_data["observatory_policy"] = self.get_data(
            self.tmdata,
            capability=osd_file_mapping["observatory_policies"],
            array_assembly=array_assembly,
        )

        telescope_capabilities = self.osd_data["observatory_policy"].get(
            "telescope_capabilities", {}
        )

        if not capabilities and not array_assembly:
            capabilities_dict = telescope_capabilities
        else:
            capabilities = [cap.capitalize() for cap in capabilities]
            if array_assembly:
                capabilities_dict = {cap: array_assembly for cap in capabilities}
            else:
                capabilities_dict = {
                    cap: telescope_capabilities.get(cap, {}) for cap in capabilities
                }

        return self.osd_data, capabilities_dict

    def __get_capabilities_and_array_assembly(
        self, tmdata, telescope_capabilities_dict: dict, osd_data: dict
    ) -> dict[dict[str, Any]]:
        """This method returns osd_data dictionary as
        mentioned in constant.py variable osd_file_mapping with values
        populated

        :param tmdata: TMData class object.
        :param telescope_capabilities_dict: mid or low
        :param osd_data: dictionary with predefined keys
            and values as mentioned in constant.py
            osd_file_mapping dictionary / json response

        :returns: osd_data dictionary with values populated or
                raises OSDDataException Keyerror
        """
        cap_err_msg_list = []
        for key, value in telescope_capabilities_dict.items():
            data = self.get_data(tmdata, capability=osd_file_mapping[key.lower()])
            self.keys_list = list(data.keys())
            err_msg = None
            if self.array_assembly:
                err_msg = self.check_array_assembly(value, self.keys_list)

            if err_msg:
                cap_err_msg_list.append(err_msg)
            else:
                osd_data["capabilities"][key.lower()] = {}
                osd_data["capabilities"][key.lower()]["basic_capabilities"] = data[
                    "basic_capabilities"
                ]
                if not self.array_assembly and not self.cycle_id:
                    for array_assembly_id in self.keys_list:
                        if array_assembly_id not in ["telescope", "basic_capabilities"]:
                            osd_data["capabilities"][key.lower()][
                                array_assembly_id
                            ] = data[array_assembly_id]
                else:
                    osd_data["capabilities"][key.lower()][value] = data[value]

        return osd_data, cap_err_msg_list

    def get_data(
        self,
        tmdata: TMData,
        capability: str = None,
        array_assembly: str = None,
    ) -> dict[dict[str, Any]]:
        """This method is for getting data from tmdata object and returns it
            based on capability and array_assembly i.e. mid and AA0.5

        :param tmdata: TMData class object.
        :param capability: mid or low
        :param array_assembly: in mid there are
            AA0.5, AA2 and AA1 you can give any one

        :returns: json object from tmdata
        """

        if "observatory_policies" in capability:
            return tmdata[capability].get_dict()

        else:
            return (
                tmdata[capability].get_dict()[array_assembly]
                if array_assembly
                else tmdata[capability].get_dict()
            )

    def get_osd_data(self) -> dict[dict[str, Any]]:
        """This method calls
            get_telescope_observatory_policies function,
            get_capabilities_and_array_assembly
            and returns osd_data dictionary

        :returns: osd_data dictionary with values populated or
                raises OSDDataException
        """

        osd_err_msg_list = []

        capabilities_and_array_assembly = None
        chk_capabilities = self.check_capabilities(self.capabilities)

        if chk_capabilities:
            osd_err_msg_list.append(chk_capabilities)
        else:
            (
                osd_data,
                telescope_capabilities_dict,
            ) = self.get_telescope_observatory_policies(
                self.capabilities, self.array_assembly
            )

            if not self.cycle_id:
                del osd_data["observatory_policy"]

            (
                capabilities_and_array_assembly,
                err_msg,
            ) = self.__get_capabilities_and_array_assembly(
                self.tmdata, telescope_capabilities_dict, osd_data
            )
            if err_msg:
                osd_err_msg_list.extend(err_msg)

        return capabilities_and_array_assembly, osd_err_msg_list

    def check_array_assembly(self, value: str, key_list: dict) -> None:
        """This method checks whether a array_assembly value like
            AA0.5 or AA1 in key_list dictionary exists or not and
            raises OSDDataException

        :returns: None or raises OSDDataException
        """
        if value not in key_list:
            msg = ", ".join(
                key for key in key_list if re.match(ARRAY_ASSEMBLY_PATTERN, key)
            )
            return ARRAY_ASSEMBLY_DOESNOT_EXIST_ERROR_MESSAGE.format(value, msg)


def check_cycle_id(
    cycle_id: int = None,
    osd_version: str = None,
    gitlab_branch: str = None,
) -> str:
    """This function checks if a given cycle exists or not
        also raises OSDDataException if gitlab_branch and osd_version
        both is given. raises OSDDataException for Cycle ID exists
        or not. and returns osd_version

    :param cycle_id: cycle id integer value.
    :param osd_version: osd version i.e. 1.9.0
    :param gitlab_branch: branch name like master, dev etc.

    :returns: osd_version in string format i.e 1.9.0
            or raises OSDDataException
    """
    cycle_error_msg_list = []

    if gitlab_branch is not None and osd_version is not None:
        cycle_error_msg_list.append(
            CYCLE_ERROR_MESSAGE,
        )

    if gitlab_branch is not None:
        osd_version = gitlab_branch

    if cycle_id is None and osd_version is None and gitlab_branch is None:
        osd_version = version("ska_ost_osd")

    versions_dict = read_json(osd_file_mapping["cycle_to_version_mapping"])
    cycle_ids = [int(key.split("_")[-1]) for key in versions_dict]
    cycle_id_exists = [cycle_id if cycle_id in cycle_ids else None][0]
    string_ids = ",".join([str(i) for i in cycle_ids])

    if cycle_id is not None and cycle_id_exists is None:
        cycle_error_msg_list.append(
            CYCLE_ID_ERROR_MESSAGE.format(cycle_id, string_ids),
        )

    elif cycle_id is not None and osd_version is None:
        osd_version = versions_dict[f"cycle_{cycle_id}"][0]

    elif cycle_id is not None and cycle_id_exists and osd_version is not None:
        if osd_version not in versions_dict[f"cycle_{cycle_id}"]:
            cycle_error_msg_list.append(
                OSD_VERSION_ERROR_MESSAGE.format(
                    osd_version, versions_dict[f"cycle_{cycle_id}"]
                )
            )

    return osd_version, cycle_error_msg_list


def osd_tmdata_source(
    cycle_id: int = None,
    osd_version: str = None,
    source: str = "car",
    gitlab_branch: str = None,
) -> str:
    """This function checks and returns source_uri for TMData class

    :param cycle_id: cycle id integer value.
    :param osd_version: osd version i.e. 1.9.0 or
        branch name like master, dev etc.
    :param source: where to get OSD Data
        from car or file
    :param gitlab_branch: branch name like master, dev etc.

    :returns: source_uris as a string or raises exception
    """
    source_error_msg_list = []

    if source not in SOURCES:
        source_msg = ", ".join(SOURCES)
        source_error_msg_list.append(AVAILABLE_SOURCE_ERROR_MESSAGE.format(source_msg))

    if (
        gitlab_branch
        and isinstance(gitlab_branch, str)
        and (source == "car" or source == "file")
    ):
        source_error_msg_list.append(SOURCE_ERROR_MESSAGE.format(source))

    osd_version, cycle_error_msg_list = check_cycle_id(
        cycle_id, osd_version, gitlab_branch
    )

    source_error_msg_list.extend(cycle_error_msg_list)

    source_url = (f"{source}:{BASE_URL}{CAR_URL}{osd_version}#{BASE_FOLDER_NAME}",)

    if source == "file":
        source_url = (f"file://{BASE_FOLDER_NAME}",)

    if source == "car":
        source_url = (f"{source}:{CAR_URL}{osd_version}#{BASE_FOLDER_NAME}",)

    return source_url, source_error_msg_list


def get_osd_data(
    capabilities: list = None,
    array_assembly: str = None,
    tmdata: TMData = None,
    cycle_id: int = None,
) -> dict[dict[str, Any]]:
    """This function creates OSD class object and returns
        osd_data dictionary as json object

    :param capabilities: mid or low
    :param array_assembly: in mid there are
        AA0.5, AA2 and AA1 you can give any one
    :param tmdata: TMData class object.

    :returns: json object
    """
    osd_data, data_error_msg_list = OSD(
        capabilities=capabilities,
        array_assembly=array_assembly,
        tmdata=tmdata,
        cycle_id=cycle_id,
    ).get_osd_data()

    return osd_data, data_error_msg_list


def update_storage(body: Dict) -> Dict:
    """This function processes and validates OSD data for insertion
    into the capabilities file

    Args:
        body (Dict): A dictionary containing the OSD data to insert

    Returns:
        Dict: A dictionary with the processed capabilities data

    Raises:
        OSDModelError: If validation fails
        ValueError: If required data is missing or invalid
    """
    mid_capabilities = {}
    result = {}
    if not body.get("capabilities", {}).get("mid"):
        return mid_capabilities

    capabilities = body["capabilities"]
    telescope = next(iter(capabilities.keys()))
    telescope_data = capabilities[telescope]

    mid_capabilities.update(
        {
            "telescope": telescope,
            "basic_capabilities": telescope_data["basic_capabilities"],
            **{
                key: telescope_data[key]
                for key in telescope_data
                if re.match(ARRAY_ASSEMBLY_PATTERN, key)
            },
        }
    )
    capabilities_path = (
        MID_CAPABILITIES_JSON_PATH if telescope == "mid" else LOW_CAPABILITIES_JSON_PATH
    )
    mid_capabilities["telescope"] = mid_capabilities["telescope"].title()
    update_file(capabilities_path, mid_capabilities)
    update_file(OBSERVATORY_POLICIES_JSON_PATH, body["observatory_policy"])
    result.update(mid_capabilities)
    result.update(body["observatory_policy"])
    return mid_capabilities


def get_osd_using_tmdata(
    cycle_id: Optional[int] = None,
    osd_version: Optional[str] = None,
    source: Optional[str] = None,
    gitlab_branch: Optional[str] = None,
    capabilities: Optional[str] = None,
    array_assembly: Optional[str] = None,
) -> dict:
    """
    Retrieve OSD data using TMData.

    Args:
        cycle_id (int, optional): Cycle ID.
        osd_version (str, optional): OSD version.
        source (str, optional): Source.
        gitlab_branch (str, optional): GitLab branch.
        capabilities (str, optional): Capabilities.
        array_assembly (str, optional): Array assembly.

    Returns:
        Dict[Dict[str, Any]]: OSD data.

    Raises:
        ValueError: If any validation or processing errors occur.
    """
    errors = []

    try:
        OSDModel(
            source=source,
            cycle_id=cycle_id,
            osd_version=osd_version,
            capabilities=capabilities,
            array_assembly=array_assembly,
        )
    except OSDModelError as error:
        errors.extend(error.args[0])

    _, cycle_errors = check_cycle_id(
        cycle_id=cycle_id,
        osd_version=osd_version,
        gitlab_branch=gitlab_branch,
    )
    if cycle_errors:
        errors.extend(cycle_errors)
        raise ValueError(errors)
    tm_data_source, error = osd_tmdata_source(
        cycle_id=cycle_id,
        osd_version=osd_version,
        source=source,
        gitlab_branch=gitlab_branch,
    )

    if error:
        errors.extend(error)

    if errors:
        raise ValueError(errors)

    tm_data = TMData(source_uris=tm_data_source)

    osd_data, osd_errors = get_osd_data(
        capabilities=[capabilities] if capabilities else None,
        tmdata=tm_data,
        array_assembly=array_assembly,
        cycle_id=cycle_id,
    )
    errors.extend(osd_errors)
    if errors:
        raise ValueError(errors)
    return osd_data
