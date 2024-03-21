import re
from dataclasses import dataclass

from ska_oso_osd.osd.constant import error_msg_list

capabilities_list = ["mid", "low"]
osd_version_pattern = r"^\d+\.\d+\.\d+"
array_assembly_pattern = r"^AA(\d+|\d+\.\d+)"


@dataclass
class QueryParams:
    """
    QueryParams is an abstract class
    """


@dataclass
class UserQuery(QueryParams):
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
            else:
                error_msg_list.append(
                    ValueError(
                        "Parameters are missing or not currently supported for"
                        " querying."
                    )
                )

        error_msg_list = osd_validation(  # pylint: disable=W0621
            params_in_kwargs, kwargs
        )

        return UserQuery(**kwargs), error_msg_list


def osd_validation(params_in_kwargs, kwargs: dict) -> dict:
    if params_in_kwargs("cycle_id") and params_in_kwargs("source"):
        if kwargs.get("source"):
            source = kwargs.get("source")
        else:
            kwargs["source"] = "file"

    if (
        params_in_kwargs("capabilities")
        or params_in_kwargs("osd_version")
        or params_in_kwargs("gitlab_branch")
        or params_in_kwargs("array_assembly")
    ):
        capability = kwargs["capabilities"] if kwargs.get("capabilities") else None
        osd_version = kwargs["osd_version"] if kwargs.get("osd_version") else None
        array_assembly = (
            kwargs["array_assembly"] if kwargs.get("array_assembly") else None
        )

        if capability not in capabilities_list:
            error_msg_list.append(
                ValueError(
                    f"Capability {capability} doesn't exists,Available are"
                    f" {', '.join(capabilities_list)}"
                )
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
