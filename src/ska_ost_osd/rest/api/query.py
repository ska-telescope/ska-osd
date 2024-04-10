import re
from dataclasses import dataclass

from ska_ost_osd.osd.constant import (
    ARRAY_ASSEMBLY_PATTERN,
    OSD_VERSION_PATTERN,
    QUERY_FIELDS,
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
        err_msg_dict = {"err_msg": []}

        def params_in_kwargs(allowed_fields: set) -> bool:
            """
            Currently the query functionality only supports a single
            type of QueryParam. This method checks that the allowed fields
            are present in the kwargs and that no other fields are also present,
            raising an error for the user if they are.
            """
            if allowed_fields in QUERY_FIELDS:
                return True
            else:
                raise ValueError(
                    "Different query types are not currently supported - for"
                    " example, cannot combine osd_version and gitlab_branch."
                )

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
            osd_version = kwargs.get("osd_version", None)
            array_assembly = kwargs.get("array_assembly", None)

            if (
                params_in_kwargs("source")
                and params_in_kwargs("osd_version")
                and osd_version is not None
            ):
                if source != "gitlab" and not re.match(
                    OSD_VERSION_PATTERN, osd_version
                ):
                    err_msg_dict["err_msg"].append(
                        f"osd_version {osd_version} is not valid"
                    )

            if array_assembly is not None:
                if not re.match(ARRAY_ASSEMBLY_PATTERN, array_assembly):
                    err_msg_dict["err_msg"].append(
                        f"array_assembly {array_assembly} is not valid"
                    )

        return UserQuery(**kwargs), err_msg_dict
