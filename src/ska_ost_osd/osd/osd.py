import copy
import re
from typing import Any, Dict, Optional

from ska_telmodel.data import TMData

from ska_ost_osd.common.utils import update_file
from ska_ost_osd.osd.common.error_handling import OSDModelError
from ska_ost_osd.osd.common.osd_validation_messages import (
    ARRAY_ASSEMBLY_DOESNOT_EXIST_ERROR_MESSAGE,
    AVAILABLE_SOURCE_ERROR_MESSAGE,
    CAPABILITY_DOESNOT_EXIST_ERROR_MESSAGE,
    CYCLE_ERROR_MESSAGE,
    CYCLE_ID_ERROR_MESSAGE,
    OSD_VERSION_ERROR_MESSAGE,
    SOURCE_ERROR_MESSAGE,
)
from ska_ost_osd.osd.common.utils import get_osd_latest_version
from ska_ost_osd.osd.models.models import OSDModel

from .common.constant import (
    ARRAY_ASSEMBLY_PATTERN,
    BASE_FOLDER_NAME,
    BASE_URL,
    CAR_URL,
    GITLAB_SOURCE,
    MID_CAPABILITIES_JSON_PATH,
    OBSERVATORY_POLICIES_JSON_PATH,
    SOURCES,
    VERSION_FILE_PATH,
    osd_file_mapping,
    osd_response_template,
)


class OSD:
    """Initialize OSD-related variables and methods, including
    get_telescope_observatory_policies, get_data, and get_osd_data."""

    def __init__(
        self, capabilities: list, array_assembly: str, tmdata: TMData, cycle_id: int
    ) -> None:
        """Initialize the OSD class.

        :param capabilities: list, capabilities of the telescope ("mid"
            or "low").
        :param array_assembly: str, for "mid" can be one of "AA0.5",
            "AA2", or "AA1".
        :param tmdata: TMData, TMData class object.
        :param cycle_id: int, cycle identifier.
        :return: None
        """
        self.cycle_id = cycle_id
        self.osd_data = copy.deepcopy(osd_response_template)
        self.capabilities = capabilities
        self.array_assembly = array_assembly
        self.tmdata = tmdata
        self.keys_list = {}

    def check_capabilities(self, capabilities: list = None) -> None:
        """Check if the given capabilities exist, and raise an exception if
        not.

        :param capabilities: list, capabilities such as "mid", "low", or
            "basic_capability".
        :return: None.
        :raises OSDDataException: If any provided capability does not
            exist.
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
        """Check if capabilities or array assembly exist, retrieve them from
        observatory policies, populate the dictionary, and return it.

        :param capabilities: list, capabilities such as "mid" or "low".
        :param array_assembly: str, for "mid" can be one of "AA0.5",
            "AA2", or "AA1".
        :return: dict, dictionary of OSD data and dictionary of
            capabilities and array assembly.
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
        """Return the osd_data dictionary with values populated as per
        osd_file_mapping.

        :param tmdata: TMData class object.
        :param telescope_capabilities_dict: dict, capabilities like
            "mid" or "low".
        :param osd_data: dict, dictionary with predefined keys and
            values as mentioned in constant.py osd_file_mapping
            dictionary / JSON response.
        :return: dict, osd_data dictionary with values populated.
            :raises OSDDataException, KeyError: If keys are missing or
            invalid.
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
        """Retrieve data from the tmdata object based on capability and array
        assembly.

        :param tmdata: TMData class object.
        :param capability: str, capability such as "mid" or "low".
        :param array_assembly: str, for "mid" can be one of "AA0.5",
            "AA2", or "AA1".
        :return: dict, JSON object from tmdata.
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
        """Call get_telescope_observatory_policies and
        get_capabilities_and_array_assembly, then return the populated osd_data
        dictionary.

        :return: dict, osd_data dictionary with values populated.
        :raises OSDDataException: If any capability check or data
            retrieval fails.
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
        """Check whether an array_assembly value like "AA0.5" or "AA1" exists
        in key_list, and raise OSDDataException if not.

        :param value: str, the array_assembly value to check.
        :param key_list: dict, dictionary keys to validate against.
        :return: None or raises OSDDataException.
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
    versions_dict: Dict = None,
) -> str:
    """This function checks if a given cycle exists or not also raises
    OSDDataException if gitlab_branch and osd_version both is given. raises
    OSDDataException for Cycle ID exists or not. and returns osd_version.

    :param cycle_id: cycle id integer value.
    :param osd_version: osd version i.e. 1.9.0
    :param gitlab_branch: branch name like master, dev etc.
    :param versions_dict: version dict containing version data
    :return: osd_version in string format i.e 1.9.0 or raises
        OSDDataException
    """
    cycle_error_msg_list = []

    if gitlab_branch is not None and osd_version is not None:
        cycle_error_msg_list.append(
            CYCLE_ERROR_MESSAGE,
        )

    if gitlab_branch is not None:
        osd_version = gitlab_branch

    if cycle_id is None and osd_version is None and gitlab_branch is None:
        osd_version = (
            get_osd_latest_version()
        )  # get latest version from latest_release.txt file

    if versions_dict is None:
        versions_dict = {}

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
    versions_dict: Dict = None,
) -> str:
    """This function checks and returns source_uri for TMData class.

    :param cycle_id: cycle id integer value.
    :param osd_version: osd version i.e. 1.9.0 or branch name like
        master, dev etc.
    :param source: where to get OSD Data from car or file
    :param gitlab_branch: branch name like master, dev etc.
    :param versions_dict: version dict containing version data
    :return: source_uris as a string or raises exception
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
        cycle_id, osd_version, gitlab_branch, versions_dict
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
    """This function creates OSD class object and returns osd_data dictionary
    as json object.

    :param capabilities: mid or low
    :param array_assembly: in mid there are AA0.5, AA2 and AA1 you can
        give any one
    :param tmdata: TMData class object.
    :param cycle_id: cycle id
    :return: json object
    """
    osd_data, data_error_msg_list = OSD(
        capabilities=capabilities,
        array_assembly=array_assembly,
        tmdata=tmdata,
        cycle_id=cycle_id,
    ).get_osd_data()

    return osd_data, data_error_msg_list


def get_osd_using_tmdata(
    cycle_id: Optional[int] = None,
    osd_version: Optional[str] = None,
    source: Optional[str] = None,
    gitlab_branch: Optional[str] = None,
    capabilities: Optional[str] = None,
    array_assembly: Optional[str] = None,
) -> Dict:
    """Retrieve OSD data using TMData.

    :param cycle_id: int, optional cycle ID.
    :param osd_version: str, optional OSD version.
    :param source: str, optional source.
    :param gitlab_branch: str, optional GitLab branch.
    :param capabilities: str, optional capabilities.
    :param array_assembly: str, optional array assembly.
    :return: Dict[Dict[str, Any]], OSD data.
    :raises ValueError: If any validation or processing errors occur.
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

    tmdata_version = TMData(GITLAB_SOURCE, update=True)
    versions_dict = tmdata_version[VERSION_FILE_PATH].get_dict()
    _, cycle_errors = check_cycle_id(
        cycle_id=cycle_id,
        osd_version=osd_version,
        gitlab_branch=gitlab_branch,
        versions_dict=versions_dict,
    )
    if cycle_errors:
        errors.extend(cycle_errors)
        raise ValueError(errors)
    tm_data_source, error = osd_tmdata_source(
        cycle_id=cycle_id,
        osd_version=osd_version,
        source=source,
        gitlab_branch=gitlab_branch,
        versions_dict=versions_dict,
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


def update_file_storage(
    validated_capabilities: Dict, observatory_policy: Dict, existing_stored_data: Dict
) -> Dict:
    """Process and validate OSD data for insertion into the capabilities file.

    :param validated_capabilities: Dict, dictionary containing the
        validated capabilities.
    :param observatory_policy: Dict, dictionary containing the
        observatory policies.
    :param existing_stored_data: Dict, the existing stored capabilities
        data.
    :return: Dict, dictionary with the processed capabilities data.
    :raises OSDModelError: If validation fails.
    :raises ValueError: If required data is missing or invalid.
    """
    # Validate request body against schema

    capabilities = validated_capabilities.capabilities

    telescope = next(iter(capabilities.keys()))
    telescope_data = capabilities[telescope]

    # Create a copy of existing data to avoid modifying it directly
    updated_data = copy.deepcopy(existing_stored_data)

    # Allow new fields while preserving existing data structure
    for key, value in telescope_data.items():
        if key in updated_data:
            # Update existing fields
            if isinstance(value, dict) and isinstance(existing_stored_data[key], dict):
                updated_data[key].update(value)
            else:
                updated_data[key] = value
        else:
            # Add new fields
            updated_data[key] = value

    # Write updated data to file
    update_file(MID_CAPABILITIES_JSON_PATH, updated_data)

    if observatory_policy:
        update_file(OBSERVATORY_POLICIES_JSON_PATH, observatory_policy)

    return updated_data


def add_new_data_storage(body: Dict) -> Dict:
    """Process and validate OSD data for insertion into the capabilities file.

    :param body: Dict, dictionary containing the OSD data to insert.
    :return: Dict, dictionary with the processed capabilities data.
    :raises OSDModelError: If validation fails.
    :raises ValueError: If required data is missing or invalid.
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
    mid_capabilities["telescope"] = mid_capabilities["telescope"].title()
    update_file(MID_CAPABILITIES_JSON_PATH, mid_capabilities)
    if body.get("observatory_policy"):
        update_file(OBSERVATORY_POLICIES_JSON_PATH, body["observatory_policy"])
        result.update(body["observatory_policy"])
    result.update(mid_capabilities)
    return mid_capabilities
