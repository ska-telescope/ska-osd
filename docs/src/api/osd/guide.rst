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
    │──── observatory_policies.json
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

    ├── common
    │   ├── __init__.py
    │   ├── models.py
    │   └── utils.py
    ├── osd
    │   ├── common
    │   ├── models
    │   ├── routers
    │   ├── version_mapping
    │   │   └── cycle_gitlab_release_version_mapping.json
    │   ├── version_manager.py
    │   └── osd.py
    ├── scripts
    │   └── release.sh
    └── telvalidation
        ├── common
        ├── models
        ├── routers
        ├── __init__.py
        ├── coordinates_conversion.py
        ├── oet_tmc_validators.py
        └── semantic_validator.py


.. note::

    * Created a separate JSON file for mapping ``cycle_id`` to version number ``cycle_gitlab_release_version_mapping.json`` inside ``version_mapping`` folder.

    * OSD supports backward compatibility for all existing released versions. If someone wants to retrieve older version then
      they just need to point out that specific version in ``osd_version``.

.. note::

    Created a bash script ``release.sh`` in ``scripts`` folder.


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
     - ``/ska-ost-osd/osd/api/v<majorversion>/osd/``
     - **Getting Data**

       Return the OSD cycle_id data



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

    "/ska-ost-osd/osd/api/v<majorversion>/osd?cycle_id=1&capabilities=mid&array_assembly=AA2"


3. CURL Example Request

.. code:: python

    curl -X GET "/ska-ost-osd/osd/api/v<majorversion>/osd?cycle_id=1&capabilities=mid&array_assembly=AA2"


4. Example Response

    * The API returns a JSON object containing the matched OSD data for default AA2.

        Calling API with parameters ``cycle_id``, ``source``, ``capabilities``
        their valid inputs will return the JSON containing the matched OSD data.

    .. code:: python

        client.get(
            "/ska-ost-osd/osd/api/v<majorversion>/osd",
            query_string={
                "cycle_id": 1,
                "source": "file",
                "capabilities": "mid",
            },
        )

    * Response

    .. code:: python

        {
          "result_data": [
            {
              "observatory_policy": {
                "cycle_number": 1,
                "cycle_description": "Science Verification",
                "cycle_information": {
                  "cycle_id": "SKAO_2027_1",
                  "proposal_open": "20260327T12:00:00.000Z",
                  "proposal_close": "20260512T15:00:00.000z"
                },
                "cycle_policies": {
                  "normal_max_hours": 100
                },
                "telescope_capabilities": {
                  "Mid": "AA2",
                  "Low": "AA2"
                }
              },
              "capabilities": {
                "mid": {
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
                  },
                  "AA2": {
                    "allowed_channel_count_range_max": [
                      214748647
                    ],
                    "allowed_channel_count_range_min": [
                      1
                    ],
                    "allowed_channel_width_values": [
                      210,
                      420,
                      840,
                      1680,
                      3360,
                      6720,
                      13440,
                      26880,
                      40320,
                      53760,
                      80640,
                      107520,
                      161280,
                      215040,
                      322560,
                      416640,
                      430080,
                      645120
                    ],
                    "available_bandwidth_hz": 800000000,
                    "available_receivers": [
                      "Band_1",
                      "Band_2",
                      "Band_5a",
                      "Band_5b"
                    ],
                    "cbf_modes": [
                      "correlation",
                      "pst",
                      "pss"
                    ],
                    "max_baseline_km": 110,
                    "number_dish_ids": [
                      "SKA001",
                      "SKA008",
                      "SKA013",
                      "SKA014",
                      "SKA015",
                      "SKA016",
                      "SKA019",
                      "SKA024",
                      "SKA025",
                      "SKA027",
                      "SKA028",
                      "SKA030",
                      "SKA031",
                      "SKA032",
                      "SKA033",
                      "SKA034",
                      "SKA035",
                      "SKA036",
                      "SKA037",
                      "SKA038",
                      "SKA039",
                      "SKA040",
                      "SKA041",
                      "SKA042",
                      "SKA043",
                      "SKA045",
                      "SKA046",
                      "SKA048",
                      "SKA049",
                      "SKA050",
                      "SKA051",
                      "SKA055",
                      "SKA061",
                      "SKA063",
                      "SKA067",
                      "SKA068",
                      "SKA070",
                      "SKA075",
                      "SKA077",
                      "SKA079",
                      "SKA081",
                      "SKA082",
                      "SKA083",
                      "SKA089",
                      "SKA091",
                      "SKA092",
                      "SKA095",
                      "SKA096",
                      "SKA097",
                      "SKA098",
                      "SKA099",
                      "SKA100",
                      "SKA101",
                      "SKA102",
                      "SKA103",
                      "SKA104",
                      "SKA106",
                      "SKA108",
                      "SKA109",
                      "SKA113",
                      "SKA114",
                      "SKA123",
                      "SKA125",
                      "SKA126"
                    ],
                    "number_fsps": 35,
                    "number_meerkat_dishes": 20,
                    "number_meerkatplus_dishes": 0,
                    "number_pss_beams": 385,
                    "number_pst_beams": 6,
                    "number_ska_dishes": 64,
                    "number_zoom_channels": 14880,
                    "number_zoom_windows": 17,
                    "ps_beam_bandwidth_hz": 800000000
                  }
                }
              }
            }
          ],
          "result_status": "success",
          "result_code": 200
        }


5. Scenarios

    1. If no parameters are provided to the API then it should return error message for required
    ``cycle_id`` or ``capabilities``.

    2. Calling API with only one parameter cycle_id and no other parameter. First it will check if the
       cycle id is valid or not, and will fetch latest version stored in the
       ``cycle_gitlab_release_version_mapping.json`` file.

    3. If source is not provided in the API call, the default is set to car. API will
       fetch data from car. other option is file and gitlab.
       If ``source`` is 'gitlab' and ``gitlab_branch`` is 'main' then it will fetch data from main branch.
       If ``source`` is 'car' then API will fetch data from Car Gitlab repo.

    4. If ``osd_version`` and ``gitlab_branch`` are given together then API will return appropriate error message.

    5. If ``cycle_id`` and ``array_assembly`` are provided together then API will return appropriate error message.


GET /cycle
==========================

.. list-table:: OSD REST resources
   :widths: 5 15 80
   :header-rows: 1

   * - HTTP Method
     - Resource URL
     - Description
   * - GET
     - ``/ska-ost-osd/osd/api/v<majorversion>/cycle``
     - **Getting Data**

       Return the OSD cycle_id data.


1. Query Parameters

  * The API supports the following query parameters to filter the OSD data:

    ===================    ============================================================
    Parameters             Description
    ===================    ============================================================
    cycle_id               Cycle Id with integer value 1, 2, 3
    ===================    ============================================================


2. For example:

.. code:: python

    "/ska-ost-osd/osd/api/v<majorversion>/cycle"


3. CURL Example Request

.. code:: python

    curl -X GET "/ska-ost-osd/osd/api/v<majorversion>/cycle"


4. Example Response

    * The API returns a JSON object containing the matched OSD data for default AA2.

        Calling API with parameters ``cycle_id`` and their valid inputs will return the JSON containing the matched OSD data.

    .. code:: python

        client.get(
            "/ska-ost-osd/osd/api/v<majorversion>/cycle"
         )

    * Response

    .. code:: python

        {
        "result_data":
            {
            "cycles": [
                1
            ]
            },
        "result_status": "success",
        "result_code": 200
        }


5. Scenarios

    1. When this api gets called the api returns all available ``cycle_id``.


POST /osd_release
==========================

.. list-table:: OSD REST resources
   :widths: 5 15 80
   :header-rows: 1

   * - HTTP Method
     - Resource URL
     - Description
   * - PUT
     - ``/ska-ost-osd/osd/api/v<majorversion>/osd/``
     - **Updating Data**

       Update the OSD capabilities data.


1. Query Parameters

  * The API supports the following query parameters to update the OSD data:

    ===================    ============================================================
    Parameters             Description
    ===================    ============================================================
    cycle_id               Cycle Id a integer value 1, 2, 3
    release_type           Major and Minor
    ===================    ============================================================



2. For example:

    .. code:: python

      "/ska-ost-osd/osd/api/v<majorversion>/osd_release?cycle_id=1&release_type=minor"


3. CURL Example Request

    .. code:: python

       curl -X POST "/ska-ost-osd/osd/api/v<majorversion>/osd_release?cycle_id=1&release_type=minor"


4. Example Response

    * The POST API initiate release process.

    .. code:: python

        client.post(
            "/ska-ost-osd/osd/api/v<majorversion>/osd_release?cycle_id=1&release_type=minor",
            query_params={
                "cycle_id": 1,
                "release_type": "minor"
            },
        )

    * Response

    .. code:: python

        {
        "result_data":
            {
            "message": f"Released new version 1.0.0",
            "version": 1.0.0,
            "cycle_id": 1,
        }
        ,
        "result_status": "success",
        "result_code": 200
        }


5. Scenarios

    1. If ``cycle_id``, ``capabilities`` and ``array_assembly`` are provided together with valid data in the request body, the API will update the capabilities JSON for the specified mid/low capabilities and return a 200 OK status code with the updated resource.

    2. If ``cycle_id``, ``capabilities`` are provided together and the request body contains ``basic_capabilities``, the API will update the ``basic_capabilities`` and return a 200 OK status code.

    3. If invalid ``cycle_id`` is provided in the request, the API will return a 404 Not Found status with an appropriate error message.

    4. If an invalid ``array_assembly`` value is provided (values other than 'AA0.5', 'AA1', or 'AA2'), the API will return a 400 Bad Request status with an error message indicating the allowed ``array_assembly`` values.

    5. If the ``array_assembly`` value doesn't match the required pattern (must be 'AA' followed by a number), the API will return a 400 Bad Request status with a message indicating the correct format pattern.

    6. If the request body is missing required fields or contains invalid data formats, the API will return a 400 Bad Request status with validation error details.

    7. If the API encounters an unexpected server-side error (such as database connection failures, internal processing errors, or system-level issues), the API will return a 500 Internal Server Error status with a generic error message.

PUT /osd
==========================

.. list-table:: OSD REST resources
   :widths: 5 15 80
   :header-rows: 1

   * - HTTP Method
     - Resource URL
     - Description
   * - PUT
     - ``/ska-ost-osd/osd/api/v<majorversion>/osd/``
     - **Updating Data**

       Update the OSD capabilities data.


1. Query Parameters

  * The API supports the following query parameters to update the OSD data:

    ===================    ============================================================
    Parameters             Description
    ===================    ============================================================
    cycle_id               Cycle Id a integer value 1, 2, 3
    capabilities           Mid or Low
    array_assembly         AA0.5, AA1 or any Array Assembly
    ===================    ============================================================


2. For example:

    .. code:: python

     "/ska-ost-osd/osd/api/v<majorversion>/osd?cycle_id=1&capabilities=mid&array_assembly=AA2"


3. CURL Example Request

    .. code:: python

      curl -X PUT "/ska-ost-osd/osd/api/v<majorversion>/osd?cycle_id=1&capabilities=mid&array_assembly=AA2"


4. Example Response

    * The PUT API allows updating the OSD data by providing a JSON object in the request body.

      When calling the PUT API, provide a complete JSON object containing all required fields including
      ``cycle_id``, ``capabilities``, and ``array_assembly``. The API will replace the existing OSD data
      that matches these parameters with the new data provided in the request body.


    .. code:: python

        client.put(
            "/ska-ost-osd/osd/api/v<majorversion>/osd",
            query_string={
                "cycle_id": 1,
                "capabilities": "mid",
                "array_assembly": "AA1",
            },
        )

    * Response

    .. code:: python

            {
        "AA0.5": {
            "allowed_channel_count_range_max": [
            58982
            ],
            "allowed_channel_count_range_min": [
            1
            ],
            "allowed_channel_width_values": [
            13440
            ],
            "available_bandwidth_hz": 800000000,
            "available_receivers": [
            "Band_1",
            "Band_2"
            ],
            "cbf_modes": [
            "correlation",
            "pst"
            ],
            "max_baseline_km": 1.5,
            "number_dish_ids": [
            "SKA001",
            "SKA036",
            "SKA063",
            "SKA100"
            ],
            "number_fsps": 4,
            "number_meerkat_dishes": 0,
            "number_meerkatplus_dishes": 0,
            "number_pss_beams": 0,
            "number_pst_beams": 1,
            "number_ska_dishes": 4,
            "number_zoom_channels": 0,
            "number_zoom_windows": 0,
            "ps_beam_bandwidth_hz": 400000000
        },
        "AA1": {
            "allowed_channel_count_range_max": [
            58982
            ],
            "allowed_channel_count_range_min": [
            1
            ],
            "allowed_channel_width_values": [
            13440
            ],
            "available_bandwidth_hz": 800000000,
            "available_receivers": [
            "Band_1",
            "Band_2",
            "Band_5a",
            "Band_5b"
            ],
            "cbf_modes": [
            "correlation",
            "pst"
            ],
            "max_baseline_km": 1.5,
            "number_dish_ids": [
            "SKA001",
            "SKA036",
            "SKA046",
            "SKA048",
            "SKA063",
            "SKA077",
            "SKA081",
            "SKA100"
            ],
            "number_fsps": 8,
            "number_meerkat_dishes": 0,
            "number_meerkatplus_dishes": 0,
            "number_pss_beams": 0,
            "number_pst_beams": 1,
            "number_ska_dishes": 8,
            "number_zoom_channels": 0,
            "number_zoom_windows": 0,
            "ps_beam_bandwidth_hz": 400000000
        },
        "AA2": {
            "allowed_channel_count_range_max": [
            214748647
            ],
            "allowed_channel_count_range_min": [
            1
            ],
            "allowed_channel_width_values": [
            210,
            420,
            840,
            1680,
            3360,
            6720,
            13440,
            26880,
            40320,
            53760
            ],
            "available_bandwidth_hz": "800000000.0",
            "available_receivers": [
            "Band_1",
            "Band_2",
            "Band_5a",
            "Band_5b"
            ],
            "cbf_modes": [
            "correlation",
            "pst",
            "pss"
            ],
            "max_baseline_km": "110.0",
            "number_dish_ids": [
            "string"
            ],
            "number_fsps": 26,
            "number_meerkat_dishes": 4,
            "number_meerkatplus_dishes": 0,
            "number_pss_beams": 384,
            "number_pst_beams": 6,
            "number_ska_dishes": 64,
            "number_zoom_channels": 14880,
            "number_zoom_windows": 16,
            "ps_beam_bandwidth_hz": "800000000.0"
        },
        "basic_capabilities": {
            "dish_elevation_limit_deg": "15.0",
            "receiver_information": [
            {
                "max_frequency_hz": "350000000.0",
                "min_frequency_hz": "1050000000.0",
                "rx_id": "Band_1"
            }
            ]
        },
        "telescope": "Mid"
        }


5. Scenarios

    1. If ``cycle_id``, ``capabilities`` and ``array_assembly`` are provided together with valid data in the request body, the API will update the capabilities JSON for the specified mid/low capabilities and return a 200 OK status code with the updated resource.

    2. If ``cycle_id``, ``capabilities`` are provided together and the request body contains ``basic_capabilities``, the API will update the ``basic_capabilities`` and return a 200 OK status code.

    3. If invalid ``cycle_id`` is provided in the request, the API will return a 404 Not Found status with an appropriate error message.

    4. If an invalid ``array_assembly`` value is provided (values other than 'AA0.5', 'AA1', or 'AA2'), the API will return a 400 Bad Request status with an error message indicating the allowed ``array_assembly`` values.

    5. If the ``array_assembly`` value doesn't match the required pattern (must be 'AA' followed by a number), the API will return a 400 Bad Request status with a message indicating the correct format pattern.

    6. If the request body is missing required fields or contains invalid data formats, the API will return a 400 Bad Request status with validation error details.

    7. If the API encounters an unexpected server-side error (such as database connection failures, internal processing errors, or system-level issues), the API will return a 500 Internal Server Error status with a generic error message.



Error Handling
```````````````

.. error::

    if ``osd_version`` value is not valid following error will be raised.

    .. code:: python

        osd_version {osd_version} is not valid

    if ``capabilities`` value is not valid following error will be raised.

    .. code:: python

        Capability {capabilities} does not exists. Available are low, mid


    if ``array_assembly`` value is not valid following error will be raised.

    .. code:: python

        array_assembly {array_assembly} is not valid


.. note::

    All the error_messages are combined in a single string.

TMData Release Process using API.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

TMData releases are now handled separately from the main ska-ost-osd codebase through an automated process:

1. **Automatic Release via API**: Use the ``POST /osd_release`` endpoint to trigger automated TMData releases

2. **Version Mapping Update**: The release process creates a new entry in ``cycle_gitlab_release_version_mapping.json`` with the new version

3. **Latest Release Update**: Automatically updates ``latest_release.txt`` with the current version

4. **Automated Publishing**: TMData is published automatically through the ``tmdata_publish`` process

API Usage
^^^^^^^^^

.. code-block:: bash

    # Trigger TMData release
    curl -X POST "/ska-ost-osd/osd/api/v<majorversion>/osd_release" \
         -H "Content-Type: application/json" \
         -d '{"cycle_id": <cycle_number>, "release_type": "minor"}'

Trigger pipeline with makefile target
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Publish TMData to artifact repository
    make tmdata-publish

.. note::

    The ``push_to_gitlab`` environment variable controls TMData publishing:
    
    - ``push_to_gitlab=0``: Local environment (default) - won't publish to artifact repository
    - ``push_to_gitlab=1``: Publishes TMData to artifact repository
    
    It's not recommended to set this flag to "1" during local testing.

View TMData Releases
^^^^^^^^^^^^^^^^^^^^

To view current TMData releases: `TMData Releases <https://gitlab.com/ska-telescope/ost/ska-ost-osd/-/blob/main/tmdata/version_mapping/latest_release.txt?ref_type=heads>`_


Manual tmdata Release Steps
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
also added a ``release.sh`` file inside ``ska_ost_osd`` ``scripts`` folder which has two functions ``GetCycleId`` and ``UpdateAndAddValue``

``GetCycleId`` function gets ``cycle_number`` from ``observatory_policies.json`` file and triggers next function ``UpdateAndAddValue``
which updates or add cycle_id values in version mapping json file.

.. code:: bash

    make osd-pre-release

5. Set the Release

* `For remaining release steps click here <https://developer.skao.int/en/latest/tutorial/release-management/automate-release-process.html>`_

.. warning::

    This is a very crucial part for OSD, without this some functionality may break and exceptions and errors will be raised.


OSD Integration
===============

This section explains how to integrate and use the **ska-ost-osd** package in your project.

Installation
------------

Add the following entry under the `[tool.poetry.dependencies]` section in your `pyproject.toml`:

.. code-block:: toml

    [tool.poetry.dependencies]
    ska-ost-osd = "^<majorversion>"

This will ensure that Poetry installs the specified version (or a compatible one) of the `ska-ost-osd` package.

Usage
-----

You can import the relevant components from the package as follows:

.. code-block:: python

    from ska_ost_osd.telvalidation.common.error_handling import (
        SchematicValidationError,
    )

This allows you to catch or raise semantic validation-related exceptions when working with OSD validation workflows.
