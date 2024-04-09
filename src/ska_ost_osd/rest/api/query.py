import re
from dataclasses import dataclass

from ska_ost_osd.osd.constant import (
    array_assembly_pattern,
    error_msg_list,
    osd_version_pattern,
)


@dataclass
class QueryParams:
    """
    QueryParams is an abstract class
    """


@dataclass
class UserQuery(QueryParams):
    """
    Class to represent a user query.

    This class stores parameters for querying OSD data. It inherits
    from the QueryParams base class to validate and parse query
    string parameters.

    :param QueryParams: abstract class
    """

    cycle_id: int = None
    osd_version: str = None
    source: str = None
    gitlab_branch: str = None
    capabilities: str = None
    array_assembly: str = None


query_fields = [
    "cycle_id",
    "osd_version",
    "source",
    "gitlab_branch",
    "capabilities",
    "array_assembly",
]


class QueryParamsFactory:
    @staticmethod
    def from_dict(kwargs: dict) -> QueryParams:
        """Convert a dictionary to a QueryParams object.

        :param kwargs (dict): The dictionary to convert.

        :returns QueryParams: An instance of the QueryParams class populated
            with values from the dictionary.

        :raises TypeError: If kwargs is not a dictionary.
        """

        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        def params_in_kwargs(field: str) -> bool:
            """
            Currently the query functionality only supports a single type of QueryParam.
            This method checks that the allowed fields are present in the kwargs
            and that no other fields are also present, raising an error for the user
            if they are.
            """

            if field in query_fields:
                return True

        error_msg_list = osd_validation(  # pylint: disable=W0621
            params_in_kwargs, kwargs
        )

        return UserQuery(**kwargs), error_msg_list


def osd_validation(params_in_kwargs, kwargs: dict) -> dict:
    """Validate parameters passed to the OSD API.

    :param params_in_kwargs (dict): The parameters passed to the API endpoint.
    :param kwargs (dict): Additional keyword arguments.

    :returns dict: The validated parameters.

    :raises ValueError: If any required parameters are missing or invalid.
    """

    if params_in_kwargs("cycle_id") and params_in_kwargs("source"):
        if kwargs.get("source"):
            source = kwargs.get("source")

    if any(
        [
            params_in_kwargs("capabilities"),
            params_in_kwargs("osd_version"),
            params_in_kwargs("gitlab_branch"),
            params_in_kwargs("array_assembly"),
        ]
    ):
        osd_version = kwargs["osd_version"] if kwargs.get("osd_version") else None
        array_assembly = (
            kwargs["array_assembly"] if kwargs.get("array_assembly") else None
        )

        if (
            params_in_kwargs("source")
            and params_in_kwargs("osd_version")
            and osd_version is not None
        ):
            if source != "gitlab" and not re.match(osd_version_pattern, osd_version):
                error_msg_list.append(
                    ValueError(f"osd_version {osd_version} is not valid")
                )

        if array_assembly is not None:
            if not re.match(array_assembly_pattern, array_assembly):
                error_msg_list.append(
                    ValueError(f"array_assembly {array_assembly} is not valid")
                )

    return error_msg_list
