OSD Model
-------------------

In its simplest form OSD consists of a set of science domain configuration files that are required by the OSO tools.
These configuration files hold slowly changing information that is used to configure the science domain behavior of each tool.
E.g. tools such as the PPT and ODT can use the information for constructing GUIs and validating setups, the Planning Tool can use it to inform itself of the capabilities available.
The idea of OSD is to provide a single source of truth for these data.


.. contents::


Introduction
~~~~~~~~~~~~~
Here we have created 'Observatory Static Data (OSD) Module'.

For creating this framework there are some requirements and architecture have already provided.
These are as follows:

* `Observatory Static Data (OSD) <https://confluence.skatelescope.org/pages/viewpage.action?spaceKey=SWSI&title=Observatory+Static+Data>`_
* `OSD Documentation Confluence Page <https://confluence.skatelescope.org/display/SE/%5BDraft%5D+OSD+documentation>`_


Folder Structure
~~~~~~~~~~~~~~~~~

.. code-block:: bash

    tmdata
    ├── osd_data
    │   ├── observatory_policies.json
    │   ├── ska1_low
    │   │   └── low_capabilities.json
    │   └── ska1_mid
    │       └── mid_capabilities.json


* `mid_capabilities.json <https://confluence.skatelescope.org/pages/viewpage.action?spaceKey=SWSI&title=Observatory+Static+Data>`_

* `low_capabilities.json <https://confluence.skatelescope.org/pages/viewpage.action?spaceKey=SWSI&title=Observatory+Static+Data>`_

* `observatory_policies.json <https://confluence.skatelescope.org/pages/viewpage.action?spaceKey=SWSI&title=Observatory+Static+Data>`_

.. note::

    ``observatory_policies.json`` is at root, because its common for both Mid and Low.

General Structure
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    ├── constant.py
    ├── helper.py
    ├── __init__.py
    ├── osd.py
    ├── resource
    │   └── release.sh
    └── version_mapping
        └── cycle_gitlab_release_version_mapping.json


.. note::

    * Created a separate JSON file for mapping ``cycle_id`` to version number ``cycle_gitlab_release_version_mapping.json`` inside ``version_mapping`` folder.
    
    * OSD supports backward compatibility for all existing released verisons. If someone wants to retrieve older version then 
      they just need to point out that specific version in ``osd_verison``.
      

.. note::

    Created a bash script ``release.sh`` in ``resource`` folder.


If user wants to access this framework from CDM, Jupyter Notebook or any other client below is the example.
If there is any error then the end user will get the appropriate error message.

This framework can be access by below command:

.. code::

    from ska_telmodel.data import TMData
    from ska_ost_osd.osd.osd import osd_tmdata_source, get_osd_data

    source_uris = osd_tmdata_source()
    tmdata = TMData(source_uris=source_uris)
    osd_data = get_osd_data(tmdata=tmdata)


* `Location of this framework <https://gitlab.com/ska-telescope/ska-ost-osd/-/tree/master/src/ska_ost_osd/telvalidation>`_

===================    ============================================================
Parameters             Description
===================    ============================================================
cycle_id               Cycle Id a integer value 1, 2, 3
osd_version            OSD version i.e 1.9.0, 1.12.0 in string format
source                 From where to get OSD data ``car`` or ``gitlab`` or ``file``
capabilities           Mid or Low
array_assembly         AA0.5, AA1 or any Array Assembly
===================    ============================================================


.. autofunction:: ska_ost_osd.osd.osd.get_osd_data

.. autofunction:: ska_ost_osd.osd.osd.OSD


API json response template
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: json

    {
    "observatory_policy": {
      "cycle_number": 1,
    "telescope_capabilities": []},
    "capabilities": {
      "mid": {},
      "low": {}}
    }


======================    ============================================================================================================
Keys                      Description
======================    ============================================================================================================
observatory_policy        file content of ``observatory_policies.json`` file
telescope_capabilities    value of ``telescope_capabilities`` in file ``observatory_policies.json``
capabilities              key value pair of mid and low
Mid                       file content of ``mid_capabilities.json`` with ``basic_capabilities`` and ``Array Assembly`` AA0.5, AA1 etc
Low                       file content of ``low_capabilities.json`` with ``basic_capabilities`` and ``Array Assembly`` AA0.5, AA1 etc
======================    ============================================================================================================


Endpoints
~~~~~~~~~~~~~~~~~

GET /osd
==========================

.. list-table:: OSD REST resources
   :widths: 5 15 80
   :header-rows: 1

   * - HTTP Method
     - Resource URL
     - Description
   * - GET
     - ``/ska-ost-osd/osd/api/v2/osd/``
     - **Getting Data**

       Return the OSD cycle_id data.


1. Query Parameters

  * The API supports the following query parameters to filter the OSD data:

    ===================    ============================================================
    Parameters             Description
    ===================    ============================================================
    cycle_id               Cycle Id a integer value 1, 2, 3
    osd_version            OSD version i.e 1.9.0, 1.12.0 in string format
    source                 From where to get OSD data ``car`` or ``gitlab`` or ``file``
    gitlab_branch          Gitlab Branch Name
    capabilities           Mid or Low
    array_assembly         AA0.5, AA1 or any Array Assembly
    ===================    ============================================================


2. For example:

.. code:: python

    "/ska-ost-osd/osd/api/v2/osd?cycle_id=1&capabilities=mid&array_assembly=AA2"


3. CURL Example Request

.. code:: python

    curl -X GET "/ska-ost-osd/osd/api/v2/osd?cycle_id=1&capabilities=mid&array_assembly=AA2"


4. Example Response

    * The API returns a JSON object containing the matched OSD data for default AA2.

        Calling API with parameters ``cycle_id``, ``source``, ``capabilities``
        their valid inputs will return the JSON containing the matched OSD data.

    .. code:: python

        client.get(
            "/ska-ost-osd/osd/api/v2/osd",
            query_string={
                "cycle_id": 1,
                "source": "file",
                "capabilities": "mid",
            },
        )

    * Response

    .. code:: python

        {
             "capabilities": {
                "mid": {
                "AA2": {
                    "available_receivers": [
                    "Band_1",
                    "Band_2",
                    "Band_5a",
                    "Band_5b"
                ],
                "number_ska_dishes": 64,
                "number_meerkat_dishes": 4,
                "number_meerkatplus_dishes": 0,
                "max_baseline_km": 110.0,
                "available_bandwidth_hz": 800000.0,
                "number_channels": 14880,
                "cbf_modes": [
                    "correlation",
                    "pst",
                    "pss"
                ],
                "number_zoom_windows": 16,
                "number_zoom_channels": 14880,
                "number_pss_beams": 384,
                "number_pst_beams": 6,
                "ps_beam_bandwidth_hz": 800000.0,
                "number_fsps": 27,
                "allowed_channel_width_values": [210, 420, 840, 1680, 3360, 6720, 13440, 26880, 40320, 53760, 80640, 107520, 161280, 215040, 322560, 416640, 430080, 645120],
                "allowed_channel_count_range_min": 1,
                "allowed_channel_count_range_max": 214748647
                },
                "basic_capabilities": {
                    "dish_elevation_limit_deg": 15,
                    "receiver_information": [
                    {
                        "max_frequency_hz": 1050000000,
                        "min_frequency_hz": 350000000,
                        "rx_id": "Band_1"
                    },
                    {
                        "max_frequency_hz": 1760000000,
                        "min_frequency_hz": 950000000,
                        "rx_id": "Band_2"
                    },
                    {
                        "max_frequency_hz": 3050000000,
                        "min_frequency_hz": 1650000000,
                        "rx_id": "Band_3"
                    },
                    {
                        "max_frequency_hz": 5180000000,
                        "min_frequency_hz": 2800000000,
                        "rx_id": "Band_4"
                    },
                    {
                        "max_frequency_hz": 8500000000,
                        "min_frequency_hz": 4600000000,
                        "rx_id": "Band_5a"
                    },
                    {
                        "max_frequency_hz": 15400000000,
                        "min_frequency_hz": 8300000000,
                        "rx_id": "Band_5b"
                    }
                    ]
                }
                }
            },
            "observatory_policy": {
                "cycle_description": "Science Verification",
                "cycle_information": {
                "cycle_id": "SKAO_2027_1",
                "proposal_close": "20260512T15:00:00.000z",
                "proposal_open": "20260327T12:00:00.000Z"
                },
                "cycle_number": 1,
                "cycle_policies": {
                "normal_max_hours": 100
                },
                "telescope_capabilities": {
                "Low": "AA2",
                "Mid": "AA2"
                }
            }
        }


5. Scenarios

    1. If no parameters are provided to the API then latest version with 
       cycle id is fetched from ``cycle_gitlab_release_version_mapping.json`` file.

    2. Calling API with only one parameter cycle_id and no other parameter. First it will check if the 
       cycle id is valid or not, and will fetch latest version stored in the 
       ``cycle_gitlab_release_version_mapping.json`` file.
    
    3. If source is not provided in the API call, the default is set to file. API will 
       fetch data from file. other option is car and gitlab. 
       If ``source`` is 'gitlab' and ``gitlab_branch`` is 'main' then it will fetch data from main branch.
       If ``source`` is 'car' then API will fetch data from Car Gitlab repo.
    
    4. If ``osd_verison`` and ``gitlab_branch`` are given together then API will return appropriate error message.

    5. If ``cycle_id`` and ``array_assembly`` are provided together then API will return appropriate error message.



Error Handling
```````````````

.. error::

    if ``osd_version`` value is not valid following error will be raised.

    .. code:: python

        osd_version {osd_version} is not valid

    if ``capabilities`` value is not valid following error will be raised.

    .. code:: python

        Capability {capabilities} doesn not exists. Available are low, mid


    if ``array_assembly`` value is not valid following error will be raised.

    .. code:: python

        array_assembly {array_assembly} is not valid


.. note::

    All the error_messages are combined in a single string.


Release Steps
~~~~~~~~~~~~~~

1. Create a JIRA issue and the branch

    1st: Create a new issue on the Release Management Jira Project with a summary of your release, and set it to “IN PROGRESS”.

    2nd: Create and checkout a new rel-XXX-release-v-1-2-2 branch (where REL-XXX is your Jira issue.)

2. Check the Current Version

.. code:: bash

    make show-version

3. Bump the Version

.. code:: bash

    make bump-patch-release

4. Run below command for OSD release

Created a target called ``osd-pre-release`` in Makefile which will run when ska_ost_osd is released.
also added a ``release.sh`` file inside ``osd`` ``resources`` folder which has two functions ``GetCycleId`` and ``UpdateAndAddValue``

``GetCycleId`` function gets ``cycle_number`` from ``observatory_policies.json`` file and triggers next function ``UpdateAndAddValue``
which updates or add cycle_id values in version mapping json file.

.. code:: bash

    make osd-pre-release

5. Set the Release

* `For remaining release steps click here <https://developer.skao.int/en/latest/tutorial/release-management/automate-release-process.html>`_

.. warning::

    This is a very crucial part for OSD, without this some functionality may break and exceptions and errors will be raised.