"""
Functions which the HTTP requests to individual resources are mapped to.

See the operationId fields of the Open API spec for the specific mappings.
"""

from http import HTTPStatus

from ska_telmodel.data import TMData

from ska_osd.osd.osd import get_osd_data, osd_tmdata_source


def get_osd(**kwargs):
    """ """
    # TODO write query param factory for better code  structure
    # implementaion written in ODA class is QueryParamsFactory
    cycle_id = kwargs.get("cycle_id")
    gitlab_branch = kwargs.get("gitlab_branch")
    source = kwargs.get("source")
    osd_version = kwargs.get("osd_version")
    capabilities = kwargs.get("capabilities")
    array_assembly = kwargs.get("array_assembly")

    tm_data_sources = osd_tmdata_source(
        cycle_id=cycle_id,
        osd_version=osd_version,
        source=source,
        gitlab_branch=gitlab_branch,
    )
    tm_data = TMData(source_uris=tm_data_sources, update=False)
    tmdata_1_gitlab_data = get_osd_data(
        capabilities=[capabilities], tmdata=tm_data, array_assembly=array_assembly
    )

    return tmdata_1_gitlab_data, HTTPStatus.OK
