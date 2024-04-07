import copy
import re
from importlib.metadata import version
from typing import Any

from ska_telmodel.data import TMData

from .constant import (
    BASE_FOLDER_NAME,
    BASE_URL,
    CAR_URL,
    array_assembly_pattern,
    error_msg_list,
    osd_file_mapping,
    osd_response_template,
    source_list,
)
from .helper import OSDDataException, read_json


class OSD:

    """OSD Class for initialing OSD related variables and methods
    including get_telescope_observatory_policies, get_data and get_osd_data
    """

    def __init__(self, capabilities: list, array_assembly: str, tmdata: TMData) -> None:
        """This is initializer method for Class OSD

        :param capabilities: mid or low
        :param array_assembly: in mid there are
            AA0.5, AA2 and AA1 you can give any one
        :param tmdata: TMData class object

        :returns: None
        """

        self.osd_data = copy.deepcopy(osd_response_template)
        self.capabilities = capabilities
        self.array_assembly = array_assembly
        self.tmdata = tmdata
        self.keys_list = {}

    def check_capabilities(self, capabilities: list = None) -> None | OSDDataException:
        """This method checks if a given capability exists or not
            and raises exception

        :param capabilities: mid, low, or basic_capability

        :returns: raises OSDDataException for capabilities
        """

        capabilities_list = list(osd_file_mapping.keys())[:3]

        if capabilities is not None:
            cap_list = [i for i in capabilities if i.lower() not in capabilities_list]

        if (capabilities is not None and isinstance(capabilities, list)) and (cap_list):
            msg = ", ".join(capabilities_list)
            cap = cap_list[0]

            error_msg_list.append(
                OSDDataException(f"Capability {cap} doesn't exists,Available are {msg}")
            )

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

        capabilities_dict = {}

        if capabilities is None and array_assembly is None:
            capabilities_dict = self.osd_data["observatory_policy"][
                "telescope_capabilities"
            ]

        elif capabilities is not None and array_assembly is None:
            for capability in capabilities:
                capabilities_dict[capability.capitalize()] = self.osd_data[
                    "observatory_policy"
                ]["telescope_capabilities"][capability.capitalize()]

        elif capabilities is None and array_assembly is not None:
            capabilities_dict = self.osd_data["observatory_policy"][
                "telescope_capabilities"
            ]

            for key in capabilities_dict.keys():
                capabilities_dict[key] = array_assembly

        elif capabilities is not None and array_assembly is not None:
            for capability in capabilities:
                capabilities_dict[capability.capitalize()] = array_assembly

        return self.osd_data, capabilities_dict

    def get_capabilities_and_array_assembly(
        self, tmdata, telescope_capabilities_dict: dict, osd_data: dict
    ) -> dict[dict[str, Any]] | OSDDataException:
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

        for key, value in telescope_capabilities_dict.items():
            data = self.get_data(tmdata, capability=osd_file_mapping[key.lower()])
            self.keys_list = list(data.keys())

            self.check_array_assembly(value, self.keys_list)

            if error_msg_list:
                return error_msg_list

            osd_data["capabilities"][key.lower()] = {}

            osd_data["capabilities"][key.lower()][value] = data[value]

            osd_data["capabilities"][key.lower()]["basic_capabilities"] = data[
                "basic_capabilities"
            ]

        return osd_data

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
            return [
                tmdata[capability].get_dict()[array_assembly]
                if array_assembly is not None
                else tmdata[capability].get_dict()
            ][0]

    def get_osd_data(self) -> dict[dict[str, Any]]:
        """This method calls
            get_telescope_observatory_policies function,
            get_capabilities_and_array_assembly
            and returns osd_data dictionary

        :returns: osd_data dictionary with values populated or
                raises OSDDataException
        """

        self.check_capabilities(self.capabilities)

        (
            osd_data,
            telescope_capabilities_dict,
        ) = self.get_telescope_observatory_policies(
            self.capabilities, self.array_assembly
        )

        if error_msg_list:
            return error_msg_list

        return self.get_capabilities_and_array_assembly(
            self.tmdata, telescope_capabilities_dict, osd_data
        )

    def check_array_assembly(
        self, value: str, key_list: dict
    ) -> None | OSDDataException:
        """This method checks whether a array_assembly value like
            AA0.5 or AA1 in key_list dictionary exists or not and
            raises OSDDataException

        :returns: None or raises OSDDataException
        """
        if value not in key_list:
            msg = ", ".join(
                key for key in key_list if re.match(array_assembly_pattern, key)
            )
            error_msg_list.append(
                OSDDataException(
                    f"Array Assembly {value} doesn't exists. Available are {msg}"
                )
            )


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

    if gitlab_branch is not None and osd_version is not None:
        msg = "either osd_version or gitlab_branch"

        error_msg_list.append(OSDDataException(f"Only one parameter is needed {msg}"))

    if gitlab_branch is not None:
        osd_version = gitlab_branch

    if cycle_id is None and osd_version is None and gitlab_branch is None:
        osd_version = version("ska_telmodel")

    versions_dict = read_json(osd_file_mapping["cycle_to_version_mapping"])

    cycle_ids = [int(key.split("_")[-1]) for key in versions_dict]

    cycle_id_exists = [cycle_id if cycle_id in cycle_ids else None][0]

    string_ids = ",".join([str(i) for i in cycle_ids])

    if cycle_id is not None and cycle_id_exists is None:
        msg = f"Available IDs are {string_ids}"

        error_msg_list.append(
            OSDDataException(f"Cycle id {cycle_id} is not valid,{msg}")
        )

    elif cycle_id is not None and osd_version is None:
        osd_version = versions_dict[f"cycle_{cycle_id}"][0]

    return osd_version


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

    if source not in source_list:
        error_msg_list.append(
            OSDDataException(
                f"source is not valid available are {', '.join(source_list)}"
            )
        )

    if (
        gitlab_branch
        and isinstance(gitlab_branch, str)
        and (source == "car" or source == "file")
    ):
        error_msg_list.append(OSDDataException("source is not valid."))

    osd_version = check_cycle_id(cycle_id, osd_version, gitlab_branch)

    if error_msg_list:
        return error_msg_list

    if source == "file":
        return (f"file://{BASE_FOLDER_NAME}",)

    if source == "car":
        return (f"{source}:{CAR_URL}{osd_version}#{BASE_FOLDER_NAME}",)

    return (f"{source}:{BASE_URL}{CAR_URL}{osd_version}#{BASE_FOLDER_NAME}",)


def get_osd_data(
    capabilities: list = None,
    array_assembly: str = None,
    tmdata: TMData = None,
) -> dict[dict[str, Any]]:
    """This function creates OSD class object and returns
        osd_data dictionary as json object

    :param capabilities: mid or low
    :param array_assembly: in mid there are
        AA0.5, AA2 and AA1 you can give any one
    :param tmdata: TMData class object.

    :returns: json object
    """

    return OSD(
        capabilities=capabilities,
        array_assembly=array_assembly,
        tmdata=tmdata,
    ).get_osd_data()
