Semantic Validation
-------------------

Semantic vs Syntactic validations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Semantic validation and syntactic validation are two types of validation techniques used in software development to
ensure that data entered into a system is accurate and conforms to the requirements of the system.

Syntactic validation checks the syntax of the input data and ensures that it adheres to the prescribed format.
It checks whether the data entered is structured correctly and follows the expected syntax rules. For example,
if an input field is supposed to accept only numerical data, a syntactic validation would ensure that only
numerical characters are entered and reject any non-numeric characters.

Semantic validation, on the other hand, checks the meaning of the input data and ensures that it is valid in the
context of the system. It checks whether the input data conforms to the business rules and logic of the system.

For example, if a system requires a date to be entered, a semantic validation would ensure that the date entered is
valid, such as it's not a future date or a date that has already passed.

In summary, syntactic validation checks the structure of the data, while semantic validation checks the meaning of the data. Both types of validation are important to ensure the accuracy and integrity of data entered into a system.


Introduction
~~~~~~~~~~~~~
Here we have created 'Framework for semantic validation of observing setups'.
This framework provides semantic validation which helps to prevent the users from making errors in their setups.
This framework is supporting both MID and LOW schema validation as well as Scheduling Block(MID).

For creating this framework there are some requirements and architecture have already provided.
These are as follows:

* `Configuration Schemas (Mid) <https://confluence.skatelescope.org/pages/viewpage.action?pageId=195895122>`_

* `Configuration Schemas (Low) <https://confluence.skatelescope.org/display/SWSI/Configuration+Schemas#ConfigurationSchemas-OET%E2%86%92TMC(Low)>`_

* `Semantic Validation architecture AA0.5 <https://confluence.skatelescope.org/pages/viewpage.action?spaceKey=SWSI&title=Semantic+Validation+architecture+AA0.5>`_



JSON validator file
~~~~~~~~~~~~~~~~~~~

Four separate JSON files have been created for Mid, Low and Scheduling Block Definition (MID & LOW) schemas to store all the parameters present in assign & configure resources
along with its business rules and errors.

* `Reference of JSON validator file (Mid) <https://gitlab.com/ska-telescope/ost/ska-ost-osd/-/blob/main/tmdata/instrument/ska1_mid/validation/mid-validation-constants.json?ref_type=heads>`_

* `Reference of JSON validator file (Low) <https://gitlab.com/ska-telescope/ost/ska-ost-osd/-/blob/main/tmdata/instrument/ska1_low/validation/low-validation-constants.json?ref_type=heads>`_

* `Reference of JSON validator file (SBD-Mid) <https://gitlab.com/ska-telescope/ost/ska-ost-osd/-/blob/main/tmdata/instrument/scheduling-block/validation/mid_sbd-validation-constants?ref_type=heads>`_

* `Reference of JSON validator file (SBD-Low) <https://gitlab.com/ska-telescope/ost/ska-ost-osd/-/blob/main/tmdata/instrument/scheduling-block/validation/low_sbd-validation-constants?ref_type=heads>`_

Created a separate ``constant`` file to maintain all telvalidation constant. From there we are importing JSON validator file
in ``semantic_validator`` for Mid, Low as well as Scheduling Block Definition (MID) schemas.

Below are the commands to import JSON validator files.

.. code::

    from ska_telmodel.data import TMData

    from .constant import (
        LOW_VALIDATION_CONSTANT_JSON_FILE_PATH,
        MID_VALIDATION_CONSTANT_JSON_FILE_PATH,
        MID_SBD_VALIDATION_CONSTANT_JSON_FILE_PATH,
        LOW_SBD_VALIDATION_CONSTANT_JSON_FILE_PATH,
    )

Created a method that accepts 'interface' and 'telescope' as parameters. Inside that there is a dictionary named 'validation_constants'
which have 'key' (SKA_LOW_TELESCOPE, SKA_MID_TELESCOPE, SKA_MID_SBD, SKA_LOW_SBD) and value pair. Based on the key provided it will return JSON path as 'value'.
These keys are imported from constant.py.

.. code::

    def get_validation_data(interface: str, telescope: str) -> Optional[str]:
    """
    Get the validation constant JSON file path based on the provided interface URI.

    :param interface: str, the interface URI from the observing command input.
    :return: str, the validation constant JSON file path, or None if not found.
    """
    validation_constants = {
        SKA_LOW_TELESCOPE: LOW_VALIDATION_CONSTANT_JSON_FILE_PATH,
        SKA_MID_TELESCOPE: MID_VALIDATION_CONSTANT_JSON_FILE_PATH,
        SKA_MID_SBD: MID_SBD_VALIDATION_CONSTANT_JSON_FILE_PATH,
        SKA_LOW_SBD: LOW_SBD_VALIDATION_CONSTANT_JSON_FILE_PATH,
    }

    for key, value in validation_constants.items():
        if key in interface or key == telescope:
            return value

    # taking mid interface as default cause there is no any specific
    # key to differentiate the interface
    return validation_constants.get(SKA_MID_TELESCOPE)



Adding a new parameter in JSON validator file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Steps to add a new parameter in JSON validator file

* Locate the appropriate place in the JSON structure:
    * Identify the parent key or object where the new parameter should be added.
    * Determine the desired position for the new parameter within the parent key's object.

* Add a new key-value pair representing the parameter:
    * Structure of parameter should be parent-child.
    * Specify the name of the parameter as the key, this key represents the parent_key and it
      should contain dictionary.
    * Add additional key-value pairs within the parent_key object for the rule and error message.
      In this you can specify the business rule & error message to validate the specific key.

Example

If a user wants to add any new parameter in JSON validator file so he can take reference of this example:


.. code::

    "scan": {
            "tmc": {
                "scan_id": [
                    {
                        "rule": "scan_id == 1",
                        "error": "Invalid input for scan_id"
                    }
                ]
            }
        },


Let's take scan command as a dummy key which is currently not present in the JSON file.

Here under scan there is a dictionary which has a key named “tmc” so scan.tmc will be the
parent_key and under tmc we have a “scan_id” child key containing a list which should contain
appropriate rules and error messages.


General structure
~~~~~~~~~~~~~~~~~~~

This framework has created very dynamically and user friendly.
If user wants to access this framework from CDM or Jupyter Notebook then
he just has to import telvalidation package from import statement and call ``semantic_validate``
function and pass the appropriate parameters to this function.
If validation fails then the end user will get the list of errors.

This framework can be access by below command:

.. code::

    from ska_ost_osd.telvalidation.semantic_validator import semantic_validate


* `Location of this framework <https://gitlab.com/ska-telescope/ska-ost-osd/-/tree/master/src/ska_ost_osd/telvalidation>`_


There are some steps of this framework these are as follows:

* Step 1
    It checks the parameter in the JSON validator document which is present in tmdata package.


* Step 2
    There is a ``validate_json`` function which takes two parameters JSON file & config as a dictionary.
    It is present in ``src/ska_ost_osd/telvalidation/oet_tmc_validators``.
    Here we are using an eval term to evaluate the business rules present in the JSON file and based on
    that it raises custom errors. All the custom errors are stored in a list named ``error_msg_list``.
    At the end this function returns a list containing all the error messages.

    .. autofunction:: ska_ost_osd.telvalidation.oet_tmc_validators.validate_json

* Step 3
    There is one more function ``semantic_validate`` which takes argument as
    observing_command_input, tm_data, osd_data, interface, array_assembly and raise_semantic.
    It is present in ``src/ska_ost_osd/telvalidation/schema``.

    This function first checks for the interface, if the interface is not present then
    a warning message is logged, indicating that the ``interface`` is missing from the config.
    Additionally, a SchematicValidationError exception is raised with the same message.

    This framework allowed interface only for two commands that are ``assignresources`` &  ``configure``.
    If a user provides an incorrect or unsupported interface value, for example if user passes the
    interface for the scan command, the code will not be able to find a matching validation schema
    based on that interface. As a result, the ``validate_json`` function will not be called, and the
    ``msg_list`` variable will remain empty.

    Also this function is not supporting low telescope schema validation currently.


    .. autofunction:: ska_ost_osd.telvalidation.semantic_validator.semantic_validate



Configuring Semantic Validation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The semantic validation API endpoint ``POST /semantic_validate`` can be
enabled or disabled by configuring the validation strictness level:

* For local development, set the ``VALIDATION_STRICTNESS`` environment
  variable
* For deployments, set the ``validation_strictness`` parameter in the Helm
  ``values.yaml`` file

When enabled, semantic validation will return 200 for a semantically valid
request, otherwise 400 with a list of semantic errors. When disabled, semantic
validation will always return 200 with a message that semantic validation is
disabled.

The validation strictness level is used across multiple OSO services and also
configures schema validation strictness in ``ska-telmodel``. A summary of
the possible validation strictness levels and how they configure both
syntactic validation in ``ska-telmodel`` and semantic validation in
``ska-ost-osd`` is given below:

+------------------------+--------------------------------------------------+---------------------------+
| Validation Strictness  | Syntactic Validation (TelModel Schemas)          | Semantic Validation (OSD) |
+========================+==================================================+===========================+
| 0                      | Permissive Warnings                              | Disabled                  |
+------------------------+--------------------------------------------------+---------------------------+
| 1                      | Permissive Errors & Strict Warnings              | Disabled                  |
+------------------------+--------------------------------------------------+---------------------------+
| 2                      | Permissive & Strict Errors                       | Enabled                   |
+------------------------+--------------------------------------------------+---------------------------+

.. warning::

   From version 1.24.0 ``ska-telmodel`` schema validation strictness level 0
   will become obsolete. If validation strictness is configured to 0 then
   schema validation will instead be run at validation strictness level 1.
   Future versions of ``ska-telmodel`` may drop all validation strictness
   levels, in which case the configuration of semantic validation is also
   liable to change.


Integration of OSD API into semantic validation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Integrated OSD capabilities into semantic validation rule file currently added support for ``mid-validation-contant.json``
file and ``sbd-validation-constants.json`` all the validation constraint are fetched from OSD API.
* `Reference of OSD file <https://confluence.skatelescope.org/display/SWSI/Observatory+Static+Data>`_

Let's take one example
There is function ``semantic_validate()`` which takes arguments as observing_command_input, tm_data, osd_data, array_assembly, interface
and raise_semantic. It is present in ``src/ska_ost_osd/telvalidation/schema``. internally we  call function
``get_osd_data()`` which takes mainly three arguments capabilities, array_assembly, tmdata object
and validate command request against OSD capabilities configuration.

below is code sample to call ``semantic_validate()``

* scenario 1
    Import 'SchematicValidationError' from 'ska_ost_osd' which contains all the customized error messages
    in string format.

    .. code-block:: python

        from ska_telmodel.data import TMData
        from ska_ost_osd.telvalidation.semantic_validator import SchematicValidationError
        tmdata = TMData()
        try:
            semantic_validate(observing_command_input, tm_data, osd_data, array_assembly, interface, raise_semantic)
        except SchematicValidationError as exc:
            raise exc

* scenario 2
    If client wants to consume both OSD and semantic validation framework together for different scenarios
    in that case they can use both as specified below in the example.
    please note that in this scenario data get validated semantically with provided OSD version.
    If there is no version provided to the OSD call then data would get semantically validated with
    latest OSD configuration.
    e.g

    .. code-block:: python

        from ska_telmodel.data import TMData
        from ska_ost_osd.telvalidation.semantic_validator import SchematicValidationError
        from ska_ost_osd.osd.osd import get_osd_data
        osd_data = get_osd_data()
        tmdata = TMData()
        try:
            semantic_validate(observing_command_input, tm_data, array_assembly, interface, raise_semantic, osd_data)
        except SchematicValidationError as exc:
            raise exc

* scenario 3
    For direct integration with OSD API, you can use the router functions:

    .. code-block:: python

        from ska_ost_osd.osd.routers.api import get_osd
        from ska_ost_osd.osd.models.models import OSDQueryParams 
        
        params = OSDQueryParams(cycle=1)
        osd_data = get_osd(params)

    When querying with cycle=1, the response includes cycle 1 specific data:

    .. code-block:: json

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
                      }
                    ]
                  },
                  "AA2": {
                    "allowed_channel_count_range_max": [214748647],
                    "allowed_channel_count_range_min": [1],
                    "available_bandwidth_hz": 800000000,
                    "available_receivers": ["Band_1", "Band_2"],
                    "number_ska_dishes": 64
                  }
                }
              }
            }
          ]
        }



========================    ================================================================================
Parameters                   Description
========================    ================================================================================
observing_command_input      dictionary containing details of command input which needs semantic validation.
tm_data                      telemodel tm_data object using which we can load semantic validate json files.
array_assembly               Array assembly contains AA0.5 or AA0.1.
interface                    interface uri in observing_command_input.
raise_semantic               True(default) would need user to catch somewhere the SchematicValidationError.
osd_data                     osd_data which can be create at client side and passed externally
========================    ================================================================================


How the rules are worked after get constraints values from OSD
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Consider we are applying semantic validation rule on dish i.e length of receptor_ids <= 4.
This constraints value 4 is fetched from OSD by referring key ``number_ska_dishes``.

.. code::

    "dish": {
                "receptor_ids": [
                    {
                        "rule": "(0 < len(receptor_ids) <= number_ska_dishes)",
                        "error": "receptor_ids are too many!Current Limit is {number_ska_dishes}"
                    }
                ]
            },

Limitation
~~~~~~~~~~~

* 1
    currently we are having directly dependency on OSD key's, means developer/Observatory scientist
    always needs to remember those constraints keys and put into rule files.

* 2
    OSD version and semantic validation rule file version should be same.

if OSD keys got removed/changed and those are not in validation rule file
it will raise SchemanticValidationKeyError saying ``Invalid rule and error key passed``


Target visibility validation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are ra and dec parameters in configure resources, to validate these parameters we have created a
separate module named ``coordinates_conversion`` which converts Right Ascension and Declination to
Azimuth and Altitude.
This module contains a function ``ra_dec_to_az_el`` which has logic for this conversion.
This function has been imported in the ``validate_target_is_visible`` function which is
present in the ``oet_tmc_validators`` module.

.. autofunction:: ska_ost_osd.telvalidation.oet_tmc_validators.validate_target_is_visible


This is the main function for conversion.

.. autofunction:: ska_ost_osd.telvalidation.coordinates_conversion.ra_dec_to_az_el


Semantic Validation API Documentation
======================================
The semantic validation api exposes semantic validation functionality as a service
It allows for the semantical validation of input JSON data against a predefined schema.
This document outlines the API's endpoints, request parameters, and response structures.

Endpoints
~~~~~~~~~

POST /semantic_validation
==========================

**Summary**: Validate input JSON semantically.

**Description**: This endpoint accepts JSON data for semantic validation and returns validation results.

**Request**

- **Content Type**: ``application/json``
- **Schema**: See `SemanticValidationRequest` schema.

**Request Body**:

The request body should be structure with following parameters:

.. list-table::
   :widths: 25 10 15 40 25
   :header-rows: 1

   * - Property
     - Type
     - Required
     - Description
     - Example
   * - ``observing_command_input``
     - object
     - Yes
     - Input JSON to be validated.
     - Refer below Semantic Validation Request schema
   * - ``interface``
     - string
     - No
     - Interface version of the input JSON.
     - ``"https://schema.skao.int/ska-tmc-assignresources/2.1"``
   * - ``array_assembly``
     - string
     - No
     - Array assembly in format AA[0-9].[0-9] (default: AA0.5).
     - ``"AA0.5"``
   * - ``sources``
     - string
     - No
     - TMData source.
     - ``"car://gitlab.com/ska-telescope/ska-ost-osd?{osd_version}#tmdata"``
   * - ``raise_semantic``
     - boolean
     - No
     - Whether to raise a semantic validation error (default: true).
     - ``true``
   * - ``osd_data``
     - object
     - No
     - Observatory static data.
     - Refer below Semantic Validation Request schema

This table outlines the expected structure of the JSON object in the request body.


**Responses**

- **200 OK**

  - **Description**: Input JSON Semantically Valid or Not
  - **Content Type**: ``application/json``
  - **Schema**: See `Semantic Validation Success Response` schema.

- **400 Bad Request**

  - **Description**: Bad request due to incorrect values passed for parameters.
  - **Content Type**: ``application/json``
  - **Schema**: See `Semantic Validation Error Response` schema.

- **500 Internal Server Error**

  - **Description**: Internal server error.


Schemas
~~~~~~~

Semantic Validation Request
============================
Note: Below examples are given for MID telescope. For Low telescope need to change observing_command_input and interface.

* Example 1: valid assign resource JSON input.

.. code-block:: json

 {
  "observing_command_input": {
  "interface": "https://schema.skao.int/ska-tmc-assignresources/2.1",
  "subarray_id": 1,
  "dish": {
    "receptor_ids": [
      "SKA001",
      "SKA002"
    ]
  },
  "sdp": {
    "interface": "https://schema.skao.int/ska-sdp-assignres/0.4",
    "execution_block": {
      "eb_id": "eb-test-20220916-00000",
      "max_length": 100.0,
      "context": {},
      "beams": [{
          "beam_id": "vis0",
          "function": "visibilities"
      }],
      "scan_types": [{
        "scan_type_id": ".default",
        "beams": {
          "vis0": {
            "channels_id": "vis_channels",
            "polarisations_id": "all"
          },
          "pss1": {
            "field_id": "field_a",
            "channels_id": "pulsar_channels",
            "polarisations_id": "all"
          }
        }
      }, {
        "scan_type_id": "target:a",
        "derive_from": ".default",
        "beams": {
          "vis0": {
            "field_id": "field_a"
          }
        }
      }],
      "channels": [{
        "channels_id": "vis_channels",
        "spectral_windows": [{
          "spectral_window_id": "fsp_1_channels",
          "count": 14880,
          "start": 0,
          "stride": 2,
          "freq_min": 350000000.0,
          "freq_max": 368000000.0,
          "link_map": [[0, 0], [200, 1], [744, 2], [944, 3]]
        }]
      }],
      "polarisations": [{
        "polarisations_id": "all",
        "corr_type": ["XX", "XY", "YY", "YX"]
      }],
      "fields": [{
        "field_id": "field_a",
        "phase_dir": {
          "ra": [123, 0.1],
          "dec": [80, 0.1],
          "reference_time": "2023-02-16T01:23:45.678900",
          "reference_frame": "ICRF3"
        },
        "pointing_fqdn": "low-tmc/telstate/0/pointing"
      }]
    },
    "processing_blocks": [
      {
        "pb_id": "pb-mvp01-20200325-00001",
        "script": {
          "kind": "realtime",
          "name": "vis_receive",
          "version": "0.1.0"
        },
        "parameters": {
        }
      },
      {
        "pb_id": "pb-mvp01-20200325-00002",
        "script": {
          "kind": "realtime",
          "name": "test_realtime",
          "version": "0.1.0"
        },
        "parameters": {
        }
      },
      {
        "pb_id": "pb-mvp01-20200325-00003",
        "script": {
          "kind": "batch",
          "name": "ical",
          "version": "0.1.0"
        },
        "parameters": {
        },
        "dependencies": [
          {
            "pb_id": "pb-mvp01-20200325-00001",
            "kind": [
              "visibilities"
            ]
          }
        ],
        "sbi_ids": ["sbi-mvp01-20200325-00001"]
      },
      {
        "pb_id": "pb-mvp01-20200325-00004",
        "script": {
          "kind": "batch",
          "name": "dpreb",
          "version": "0.1.0"
        },
        "parameters": {
        },
        "dependencies": [
          {
            "pb_id": "pb-mvp01-20200325-00003",
            "kind": [
              "calibration"
            ]
          }
        ]
      }
    ],
    "resources": {
      "csp_links": [1, 2, 3, 4],
      "receptors": [
              "SKA001",
              "SKA002"
      ]
    }
  }},
  "interface": "https://schema.skao.int/ska-tmc-assignresources/2.1",
  "raise_semantic": true,
  "osd_data" : {
    "observatory_policy": {
        "cycle_number": 2,
        "cycle_description": "Science Verification",
        "cycle_information": {
            "cycle_id": "SKAO_2027_1",
            "proposal_open": "20260327T12:00:00.000Z",
            "proposal_close": "20260512T15:00:00.000z"
        },
        "cycle_policies": {"normal_max_hours": 100.0},
        "telescope_capabilities": {"Mid": "AA2", "Low": "AA2"}
    },
    "capabilities": {
        "mid": {
            "AA0.5": {
                "available_receivers": ["Band_1", "Band_2"],
                "number_ska_dishes": 4,
                "number_meerkat_dishes": 0,
                "number_meerkatplus_dishes": 0,
                "max_baseline_km": 1.5,
                "available_bandwidth_hz": 800000000.0,
                "cbf_modes": ["correlation", "pst"],
                "number_zoom_windows": 0,
                "number_zoom_channels": 0,
                "number_pss_beams": 0,
                "number_pst_beams": 1,
                "ps_beam_bandwidth_hz": 400000000.0,
                "number_fsps": 4,
                "number_dish_ids": ["SKA001", "SKA036", "SKA063", "SKA100"]
            },
            "basic_capabilities": {
                "dish_elevation_limit_deg": 15.0,
                "receiver_information": [
                    {
                        "rx_id": "Band_1",
                        "min_frequency_hz": 350000000.0,
                        "max_frequency_hz": 1050000000.0
                    },
                    {
                        "rx_id": "Band_2",
                        "min_frequency_hz": 950000000.0,
                        "max_frequency_hz": 1760000000.0
                    },
                    {
                        "rx_id": "Band_3",
                        "min_frequency_hz": 1650000000.0,
                        "max_frequency_hz": 3050000000.0
                    },
                    {
                        "rx_id": "Band_4",
                        "min_frequency_hz": 2800000000.0,
                        "max_frequency_hz": 5180000000.0
                    },
                    {
                        "rx_id": "Band_5a",
                        "min_frequency_hz": 4600000000.0,
                        "max_frequency_hz": 8500000000.0
                    },
                    {
                        "rx_id": "Band_5b",
                        "min_frequency_hz": 8300000000.0,
                        "max_frequency_hz": 15400000000.0
                    }
                ]
            }
        }
    } }}


Semantic Validation Success Response

.. code-block:: json

  {
  "result_data": "JSON is semantically valid",
  "result_status": "success",
  "result_code": 200
  }

* Example 2: Invalid MID assign resource JSON input.


In below example added extra dish into 'receptor_ids' currently allowed 4, due to addition of one more it's 5.

.. code-block:: json

  {
  "observing_command_input": {
  "interface": "https://schema.skao.int/ska-tmc-assignresources/2.1",
  "subarray_id": 1,
  "dish": {
    "receptor_ids": [
      "SKA001",
      "SKA002",
      "SKA003",
      "SKA004",
      "SKA005"
    ]
  },
  "sdp": {
    "interface": "https://schema.skao.int/ska-sdp-assignres/0.4",
    "execution_block": {
      "eb_id": "eb-test-20220916-00000",
      "max_length": 100.0,
      "context": {},
      "beams": [{
          "beam_id": "vis0",
          "function": "visibilities"
      }],
      "scan_types": [{
        "scan_type_id": ".default",
        "beams": {
          "vis0": {
            "channels_id": "vis_channels",
            "polarisations_id": "all"
          },
          "pss1": {
            "field_id": "field_a",
            "channels_id": "pulsar_channels",
            "polarisations_id": "all"
          }
        }
      }, {
        "scan_type_id": "target:a",
        "derive_from": ".default",
        "beams": {
          "vis0": {
            "field_id": "field_a"
          }
        }
      }],
      "channels": [{
        "channels_id": "vis_channels",
        "spectral_windows": [{
          "spectral_window_id": "fsp_1_channels",
          "count": 14880,
          "start": 0,
          "stride": 2,
          "freq_min": 350000000.0,
          "freq_max": 368000000.0,
          "link_map": [[0, 0], [200, 1], [744, 2], [944, 3]]
        }]
      }],
      "polarisations": [{
        "polarisations_id": "all",
        "corr_type": ["XX", "XY", "YY", "YX"]
      }],
      "fields": [{
        "field_id": "field_a",
        "phase_dir": {
          "ra": [123, 0.1],
          "dec": [80, 0.1],
          "reference_time": "2023-02-16T01:23:45.678900",
          "reference_frame": "ICRF3"
        },
        "pointing_fqdn": "low-tmc/telstate/0/pointing"
      }]
    },
    "processing_blocks": [
      {
        "pb_id": "pb-mvp01-20200325-00001",
        "script": {
          "kind": "realtime",
          "name": "vis_receive",
          "version": "0.1.0"
        },
        "parameters": {
        }
      },
      {
        "pb_id": "pb-mvp01-20200325-00002",
        "script": {
          "kind": "realtime",
          "name": "test_realtime",
          "version": "0.1.0"
        },
        "parameters": {
        }
      },
      {
        "pb_id": "pb-mvp01-20200325-00003",
        "script": {
          "kind": "batch",
          "name": "ical",
          "version": "0.1.0"
        },
        "parameters": {
        },
        "dependencies": [
          {
            "pb_id": "pb-mvp01-20200325-00001",
            "kind": [
              "visibilities"
            ]
          }
        ],
        "sbi_ids": ["sbi-mvp01-20200325-00001"]
      },
      {
        "pb_id": "pb-mvp01-20200325-00004",
        "script": {
          "kind": "batch",
          "name": "dpreb",
          "version": "0.1.0"
        },
        "parameters": {
        },
        "dependencies": [
          {
            "pb_id": "pb-mvp01-20200325-00003",
            "kind": [
              "calibration"
            ]
          }
        ]
      }
    ],
    "resources": {
      "csp_links": [1, 2, 3, 4],
      "receptors": [
              "SKA001",
              "SKA002"
      ]
    }
  }},
  "interface": "https://schema.skao.int/ska-tmc-assignresources/2.1",
  "raise_semantic": true,
  "osd_data" : {
    "observatory_policy": {
        "cycle_number": 2,
        "cycle_description": "Science Verification",
        "cycle_information": {
            "cycle_id": "SKAO_2027_1",
            "proposal_open": "20260327T12:00:00.000Z",
            "proposal_close": "20260512T15:00:00.000z"
        },
        "cycle_policies": {"normal_max_hours": 100.0},
        "telescope_capabilities": {"Mid": "AA2", "Low": "AA2"}
    },
    "capabilities": {
        "mid": {
            "AA0.5": {
                "available_receivers": ["Band_1", "Band_2"],
                "number_ska_dishes": 4,
                "number_meerkat_dishes": 0,
                "number_meerkatplus_dishes": 0,
                "max_baseline_km": 1.5,
                "available_bandwidth_hz": 800000000.0,
                "cbf_modes": ["correlation", "pst"],
                "number_zoom_windows": 0,
                "number_zoom_channels": 0,
                "number_pss_beams": 0,
                "number_pst_beams": 1,
                "ps_beam_bandwidth_hz": 400000000.0,
                "number_fsps": 4,
                "number_dish_ids": ["SKA001", "SKA036", "SKA063", "SKA100"]
            },
            "basic_capabilities": {
                "dish_elevation_limit_deg": 15.0,
                "receiver_information": [
                    {
                        "rx_id": "Band_1",
                        "min_frequency_hz": 350000000.0,
                        "max_frequency_hz": 1050000000.0
                    },
                    {
                        "rx_id": "Band_2",
                        "min_frequency_hz": 950000000.0,
                        "max_frequency_hz": 1760000000.0
                    },
                    {
                        "rx_id": "Band_3",
                        "min_frequency_hz": 1650000000.0,
                        "max_frequency_hz": 3050000000.0
                    },
                    {
                        "rx_id": "Band_4",
                        "min_frequency_hz": 2800000000.0,
                        "max_frequency_hz": 5180000000.0
                    },
                    {
                        "rx_id": "Band_5a",
                        "min_frequency_hz": 4600000000.0,
                        "max_frequency_hz": 8500000000.0
                    },
                    {
                        "rx_id": "Band_5b",
                        "min_frequency_hz": 8300000000.0,
                        "max_frequency_hz": 15400000000.0
                    }
                ]
            }
        }
    } }}

Semantic Validation Success Response With Error

.. code-block:: json

    {
    "result_data":
      [
          "receptor_ids are too many! Current Limit is 4",
          "length of receptor_ids should be same as length of receptors",
          "receptor_ids did not match receptors",
      ]
    ,
    "result_status": "failed",
    "result_code": 422
    }

* Example 3: valid SBD-Mid JSON input.

.. code-block:: json

    {
    "observing_command_input": {
    "interface": "https://schema.skao.int/ska-oso-pdm-sbd/0.1",
    "sbd_id": "sbi-mvp01-20200325-00001",
    "telescope": "ska_mid",
    "metadata": {
      "version": 1,
      "created_by": "Liz Bartlett",
      "created_on": "2022-03-28T15:43:53.971548+00:00",
      "last_modified_on": "2022-03-28T15:43:53.971548+00:00",
      "last_modified_by": "Liz Bartlett"
    },
    "activities": {
      "allocate": {
        "kind": "filesystem",
        "path": "file:///path/to/allocatescript.py",
        "function_args": {
          "init": {
            "args": [
              "posarg1",
              "posarg2"
            ],
            "kwargs": {
              "argname": "argval"
            }
          },
          "main": {
            "args": [
              "posarg1",
              "posarg2"
            ],
            "kwargs": {
              "argname": "argval"
            }
          }
        }
      },
      "observe": {
        "kind": "git",
        "path": "git://relative/path/to/scriptinsiderepo.py",
        "repo": "https://gitlab.com/script_repo/operational_scripts",
        "branch": "main",
        "function_args": {
          "init": {
            "args": [
              "posarg1",
              "posarg2"
            ],
            "kwargs": {
              "argname": "argval"
            }
          },
          "main": {
            "args": [
              "posarg1",
              "posarg2"
            ],
            "kwargs": {
              "argname": "argval"
            }
          }
        }
      }
    },
    "scan_definitions": [
      {
        "scan_definition_id": "calibrator scan",
        "scan_duration": 60000,
        "target": "Polaris Australis",
        "dish_configuration": "dish config 123",
        "scan_type": "calibration_B",
        "csp_configuration": "csp config 123"
      },
      {
        "scan_duration": 60000,
        "target": "M83",
        "dish_configuration": "dish config 123",
        "scan_type": "science_A",
        "scan_definition_id": "science scan",
        "csp_configuration": "csp config 123"
      }
    ],
    "scan_sequence": [
      "calibrator scan",
      "science scan",
      "science scan",
      "calibrator scan"
    ],
    "targets": [
      {
        "target_id": "Polaris Australis",
        "pointing_pattern": {
          "active": "FivePointParameters",
          "parameters": [
            {
              "kind": "FivePointParameters",
              "offset_arcsec": 5.0
            },
            {
              "kind": "RasterParameters",
              "row_length_arcsec": 1.23,
              "row_offset_arcsec": 4.56,
              "n_rows": 2,
              "pa": 7.89,
              "unidirectional": true
            },
            {
              "kind": "StarRasterParameters",
              "row_length_arcsec": 1.23,
              "n_rows": 2,
              "row_offset_angle": 4.56,
              "unidirectional": true
            }
          ]
        },
        "reference_coordinate": {
          "kind": "equatorial",
          "ra": "21:08:47.92",
          "dec": "-88:57:22.9",
          "reference_frame": "ICRS",
          "unit": [
            "hourangle",
            "deg"
          ]
        }
      },
      {
        "target_id": "M83",
        "pointing_pattern": {
          "active": "SinglePointParameters",
          "parameters": [
            {
              "kind": "SinglePointParameters",
              "offset_x_arcsec": 0.0,
              "offset_y_arcsec": 0.0
            }
          ]
        },
        "reference_coordinate": {
          "kind": "equatorial",
          "ra": "13:37:00.919",
          "dec": "-29:51:56.74",
          "reference_frame": "ICRS",
          "unit": [
            "hourangle",
            "deg"
          ]
        }
      }
    ],
    "sdp_configuration": {
      "execution_block": {
        "eb_id": "eb-mvp01-20200325-00001",
        "max_length": 100.0,
        "context": {
          "foo": "bar",
          "baz": 123
        },
        "beams": [
          {
            "beam_id": "vis0",
            "function": "visibilities"

          }
        ],
        "scan_types": [
          {
            "scan_type_id": ".default",
            "beams": [
              {
                "beam_id": "vis0",
                "channels_id": "vis_channels",
                "polarisations_id": "all"
              },
              {
                "beam_id": "pss1",
                "field_id": "M83",
                "channels_id": "pulsar_channels",
                "polarisations_id": "all"
              },
              {
                "beam_id": "pss2",
                "field_id": "Polaris Australis",
                "channels_id": "pulsar_channels",
                "polarisations_id": "all"
              },
              {
                "beam_id": "pst1",
                "field_id": "M83",
                "channels_id": "pulsar_channels",
                "polarisations_id": "all"
              },
              {
                "beam_id": "pst2",
                "field_id": "Polaris Australis",
                "channels_id": "pulsar_channels",
                "polarisations_id": "all"
              },
              {
                "beam_id": "vlbi",
                "field_id": "Polaris Australis",
                "channels_id": "vlbi_channels",
                "polarisations_id": "all"
              }
            ]
          },
          {
            "scan_type_id": ".default",
            "derive_from": ".default",
            "beams": [
              {
                "beam_id": "vis0",
                "field_id": "M83"
              }
            ]
          }
        ],
        "channels": [
          {
            "channels_id": "vis_channels",
            "spectral_windows": [
              {
                "spectral_window_id": "fsp_1_channels",
                "count": 14880,
                "start": 0,
                "stride": 2,
                "freq_min": 350000000,
                "freq_max": 368000000,
                "link_map": [
                  [
                    0,
                    0
                  ],
                  [
                    200,
                    1
                  ],
                  [
                    744,
                    2
                  ],
                  [
                    944,
                    3
                  ]
                ]
              }
            ]
          },
          {
            "channels_id": "pulsar_channels",
            "spectral_windows": [
              {
                "spectral_window_id": "pulsar_fsp_channels",
                "count": 14880,
                "start": 0,
                "freq_min": 350000000,
                "freq_max": 368000000
              }
            ]
          }
        ],
        "polarisations": [
          {
            "polarisations_id": "all",
            "corr_type": [
              "XX",
              "XY",
              "YY",
              "YX"
            ]
          }
        ]
      },
      "processing_blocks": [
        {
          "pb_id": "pb-mvp01-20200325-00001",
          "sbi_ids": [
            "sbi-mvp01-20200325-00001"
          ],
          "script": {
            "version": "0.1.0",
            "name": "vis_receive",
            "kind": "realtime"
          },
          "parameters": {}
        },
        {
          "pb_id": "pb-mvp01-20200325-00002",
          "sbi_ids": [
            "sbi-mvp01-20200325-00001"
          ],
          "script": {
            "version": "0.1.0",
            "name": "test_realtime",
            "kind": "realtime"
          },
          "parameters": {}
        },
        {
          "pb_id": "pb-mvp01-20200325-00003",
          "sbi_ids": [
            "sbi-mvp01-20200325-00001"
          ],
          "script": {
            "version": "0.1.0",
            "name": "ical",
            "kind": "batch"
          },
          "parameters": {},
          "dependencies": [
            {
              "pb_id": "pb-mvp01-20200325-00001",
              "kind": [
                "visibilities"
              ]
            }
          ]
        },
        {
          "pb_id": "pb-mvp01-20200325-00004",
          "sbi_ids": [
            "sbi-mvp01-20200325-00001"
          ],
          "script": {
            "version": "0.1.0",
            "name": "dpreb",
            "kind": "batch"
          },
          "parameters": {},
          "dependencies": [
            {
              "pb_id": "pb-mvp01-20200325-00003",
              "kind": [
                "calibration"
              ]
            }
          ]
        }
      ],
      "resources": {
        "csp_links": [
          1,
          2,
          3,
          4
        ],
        "receptors": [
          "0001",
          "0002"
        ],
        "receive_nodes": 10
      }
    },
    "csp_configurations": [
      {
        "config_id": "csp config 123",
        "subarray": {
          "subarray_name": "science period 23"
        },
        "common": {
          "subarray_id": 1,
          "band_5_tuning": [
            5.85,
            7.25
          ]
        },
        "cbf": {
          "fsp": [
            {
              "fsp_id": 1,
              "function_mode": "CORR",
              "frequency_slice_id": 1,
              "integration_factor": 1,
              "zoom_factor": 0,
              "channel_averaging_map": [
                [
                  0,
                  2
                ],
                [
                  744,
                  0
                ]
              ],
              "channel_offset": 0,
              "output_link_map": [
                [
                  0,
                  0
                ],
                [
                  200,
                  1
                ]
              ]
            },
            {
              "fsp_id": 2,
              "function_mode": "CORR",
              "frequency_slice_id": 2,
              "integration_factor": 1,
              "zoom_factor": 1,
              "zoom_window_tuning": 650000
            }
          ]
        }
      }
    ],
    "dish_allocations": {
      "receptor_ids": [
        "0001",
        "0002"
      ]
    },
    "dish_configurations": [
      {
        "dish_configuration_id": "dish config 123",
        "receiver_band": "1"
      }
    ]
   },
   "raise_semantic":"true",
   "osd_data": {
    "capabilities": {
      "mid": {
        "AA0.5": {
          "allowed_channel_count_range_max": [58982],
          "allowed_channel_count_range_min": [1],
          "allowed_channel_width_values": [
            13440
          ],
          "available_bandwidth_hz": 800000000.0,
          "available_receivers": [
            "Band_1",
            "Band_2"
          ],
          "cbf_modes": [
            "correlation",
            "pst"
          ],
          "max_baseline_km": 1.5,
          "number_fsps": 4,
          "number_meerkat_dishes": 0,
          "number_meerkatplus_dishes": 0,
          "number_pss_beams": 0,
          "number_pst_beams": 1,
          "number_ska_dishes": 4,
          "number_zoom_channels": 0,
          "number_zoom_windows": 0,
          "ps_beam_bandwidth_hz": 400000000.0,
          "number_dish_ids": ["SKA001", "SKA036", "SKA063", "SKA100"]
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
        "proposal_close": "2026-05-12T15:00:00.000Z",
        "proposal_open": "2026-03-27T12:00:00.000Z"
      },
      "cycle_number": 2,
      "cycle_policies": {
        "normal_max_hours": 100
      },
      "telescope_capabilities": {
        "Low": "AA2",
        "Mid": "AA2"
      }
    }
  }
  }


Semantic Validation Success Response for SBD-Mid input.

.. code-block:: json

     {
        "result_data": "JSON is semantically valid",
        "result_status": "success",
        "result_code": 200
      }

* Example 4: Invalid SBD-Mid JSON input.

.. code-block:: json

  {
  "observing_command_input": {
    "interface": "https://schema.skao.int/ska-oso-pdm-sbd/0.1",
    "sbd_id": "sbi-mvp01-20200325-00001",
    "telescope": "ska_mid",
    "metadata": {
      "version": 1,
      "created_by": "Liz Bartlett",
      "created_on": "2022-03-28T15:43:53.971548+00:00",
      "last_modified_on": "2022-03-28T15:43:53.971548+00:00",
      "last_modified_by": "Liz Bartlett"
    },
    "activities": {
      "allocate": {
        "kind": "filesystem",
        "path": "file:///path/to/allocatescript.py",
        "function_args": {
          "init": {
            "args": [
              "posarg1",
              "posarg2"
            ],
            "kwargs": {
              "argname": "argval"
            }
          },
          "main": {
            "args": [
              "posarg1",
              "posarg2"
            ],
            "kwargs": {
              "argname": "argval"
            }
          }
        }
      },
      "observe": {
        "kind": "git",
        "path": "git://relative/path/to/scriptinsiderepo.py",
        "repo": "https://gitlab.com/script_repo/operational_scripts",
        "branch": "main",
        "function_args": {
          "init": {
            "args": [
              "posarg1",
              "posarg2"
            ],
            "kwargs": {
              "argname": "argval"
            }
          },
          "main": {
            "args": [
              "posarg1",
              "posarg2"
            ],
            "kwargs": {
              "argname": "argval"
            }
          }
        }
      }
    },
    "scan_definitions": [
      {
        "scan_definition_id": "calibrator scan",
        "scan_duration": 60000,
        "target": "Polaris Australis",
        "dish_configuration": "dish config 123",
        "scan_type": "calibration_B",
        "csp_configuration": "csp config 123"
      },
      {
        "scan_duration": 60000,
        "target": "M83",
        "dish_configuration": "dish config 123",
        "scan_type": "science_A",
        "scan_definition_id": "science scan",
        "csp_configuration": "csp config 123"
      }
    ],
    "scan_sequence": [
      "calibrator scan",
      "science scan",
      "science scan",
      "calibrator scan"
    ],
    "targets": [
      {
        "target_id": "Polaris Australis",
        "pointing_pattern": {
          "active": "FivePointParameters",
          "parameters": [
            {
              "kind": "FivePointParameters",
              "offset_arcsec": 5.0
            },
            {
              "kind": "RasterParameters",
              "row_length_arcsec": 1.23,
              "row_offset_arcsec": 4.56,
              "n_rows": 2,
              "pa": 7.89,
              "unidirectional": true
            },
            {
              "kind": "StarRasterParameters",
              "row_length_arcsec": 1.23,
              "n_rows": 2,
              "row_offset_angle": 4.56,
              "unidirectional": true
            }
          ]
        },
        "reference_coordinate": {
          "kind": "equatorial",
          "ra": "21:08:47.92",
          "dec": "-88:57:22.9",
          "reference_frame": "ICRS",
          "unit": [
            "hourangle",
            "deg"
          ]
        }
      },
      {
        "target_id": "M83",
        "pointing_pattern": {
          "active": "SinglePointParameters",
          "parameters": [
            {
              "kind": "SinglePointParameters",
              "offset_x_arcsec": 0.0,
              "offset_y_arcsec": 0.0
            }
          ]
        },
        "reference_coordinate": {
          "kind": "equatorial",
          "ra": "13:37:00.919",
          "dec": "-29:51:56.74",
          "reference_frame": "ICRS",
          "unit": [
            "hourangle",
            "deg"
          ]
        }
      }
    ],
    "sdp_configuration": {
      "execution_block": {
        "eb_id": "eb-mvp01-20200325-00001",
        "max_length": 100.0,
        "context": {
          "foo": "bar",
          "baz": 123
        },
        "beams": [
          {
            "beam_id": "vis0",
            "function": "visibilities"

          }
        ],
        "scan_types": [
          {
            "scan_type_id": ".default",
            "beams": [
              {
                "beam_id": "vis0",
                "channels_id": "vis_channels",
                "polarisations_id": "all"
              },
              {
                "beam_id": "pss1",
                "field_id": "M83",
                "channels_id": "pulsar_channels",
                "polarisations_id": "all"
              },
              {
                "beam_id": "pss2",
                "field_id": "Polaris Australis",
                "channels_id": "pulsar_channels",
                "polarisations_id": "all"
              },
              {
                "beam_id": "pst1",
                "field_id": "M83",
                "channels_id": "pulsar_channels",
                "polarisations_id": "all"
              },
              {
                "beam_id": "pst2",
                "field_id": "Polaris Australis",
                "channels_id": "pulsar_channels",
                "polarisations_id": "all"
              },
              {
                "beam_id": "vlbi",
                "field_id": "Polaris Australis",
                "channels_id": "vlbi_channels",
                "polarisations_id": "all"
              }
            ]
          },
          {
            "scan_type_id": ".default",
            "derive_from": ".default",
            "beams": [
              {
                "beam_id": "vis0",
                "field_id": "M83"
              }
            ]
          }
        ],
        "channels": [
          {
            "channels_id": "vis_channels",
            "spectral_windows": [
              {
                "spectral_window_id": "fsp_1_channels",
                "count": 14880,
                "start": 0,
                "stride": 2,
                "freq_min": 350000000,
                "freq_max": 368000000,
                "link_map": [
                  [
                    0,
                    0
                  ],
                  [
                    200,
                    1
                  ],
                  [
                    744,
                    2
                  ],
                  [
                    944,
                    3
                  ]
                ]
              }
            ]
          },
          {
            "channels_id": "pulsar_channels",
            "spectral_windows": [
              {
                "spectral_window_id": "pulsar_fsp_channels",
                "count": 15000,
                "start": 0,
                "freq_min": 350000000000,
                "freq_max": 36800000000
              }
            ]
          }
        ],
        "polarisations": [
          {
            "polarisations_id": "all",
            "corr_type": [
              "XX",
              "XY",
              "YY",
              "YX"
            ]
          }
        ]
      },
      "processing_blocks": [
        {
          "pb_id": "pb-mvp01-20200325-00001",
          "sbi_ids": [
            "sbi-mvp01-20200325-00001"
          ],
          "script": {
            "version": "0.1.0",
            "name": "vis_receive",
            "kind": "realtime"
          },
          "parameters": {}
        },
        {
          "pb_id": "pb-mvp01-20200325-00002",
          "sbi_ids": [
            "sbi-mvp01-20200325-00001"
          ],
          "script": {
            "version": "0.1.0",
            "name": "test_realtime",
            "kind": "realtime"
          },
          "parameters": {}
        },
        {
          "pb_id": "pb-mvp01-20200325-00003",
          "sbi_ids": [
            "sbi-mvp01-20200325-00001"
          ],
          "script": {
            "version": "0.1.0",
            "name": "ical",
            "kind": "batch"
          },
          "parameters": {},
          "dependencies": [
            {
              "pb_id": "pb-mvp01-20200325-00001",
              "kind": [
                "visibilities"
              ]
            }
          ]
        },
        {
          "pb_id": "pb-mvp01-20200325-00004",
          "sbi_ids": [
            "sbi-mvp01-20200325-00001"
          ],
          "script": {
            "version": "0.1.0",
            "name": "dpreb",
            "kind": "batch"
          },
          "parameters": {},
          "dependencies": [
            {
              "pb_id": "pb-mvp01-20200325-00003",
              "kind": [
                "calibration"
              ]
            }
          ]
        }
      ],
      "resources": {
        "csp_links": [
          1,
          2,
          3,
          4
        ],
        "receptors": [
          "0001",
          "0002"
        ],
        "receive_nodes": 10
      }
    },
    "csp_configurations": [
      {
        "config_id": "csp config 123",
        "subarray": {
          "subarray_name": "science period 23"
        },
        "common": {
          "subarray_id": 1,
          "band_5_tuning": [
            5.85,
            7.25
          ]
        },
        "cbf": {
          "fsp": [
            {
              "fsp_id": 2,
              "function_mode": "CORR",
              "frequency_slice_id": 1,
              "integration_factor": 1,
              "zoom_factor": 0,
              "channel_averaging_map": [
                [
                  0,
                  2
                ],
                [
                  744,
                  0
                ]
              ],
              "channel_offset": 0,
              "output_link_map": [
                [
                  0,
                  0
                ],
                [
                  200,
                  1
                ]
              ]
            },
            {
              "fsp_id": 2,
              "function_mode": "CORR",
              "frequency_slice_id": 2,
              "integration_factor": 1,
              "zoom_factor": 1,
              "zoom_window_tuning": 650000
            }
          ]
        }
      }
    ],
    "dish_allocations": {
      "receptor_ids": [
        "0001",
        "0002"
      ]
    },
    "dish_configurations": [
      {
        "dish_configuration_id": "dish config 123",
        "receiver_band": "1"
      }
    ]
   },
   "raise_semantic":"true",
   "osd_data": {
    "capabilities": {
      "mid": {
        "AA0.5": {
          "allowed_channel_count_range_max": [58982],
          "allowed_channel_count_range_min": [1],
          "allowed_channel_width_values": [
            13440
          ],
          "available_bandwidth_hz": 800000000.0,
          "available_receivers": [
            "Band_1",
            "Band_2"
          ],
          "cbf_modes": [
            "correlation",
            "pst"
          ],
          "max_baseline_km": 1.5,
          "number_fsps": 4,
          "number_meerkat_dishes": 0,
          "number_meerkatplus_dishes": 0,
          "number_pss_beams": 0,
          "number_pst_beams": 1,
          "number_ska_dishes": 4,
          "number_zoom_channels": 0,
          "number_zoom_windows": 0,
          "ps_beam_bandwidth_hz": 400000000.0,
          "number_dish_ids": ["SKA001", "SKA036", "SKA063", "SKA100"]
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
              "max_frequency_hz": 518000000000,
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
        "proposal_close": "2026-05-12T15:00:00.000Z",
        "proposal_open": "2026-03-27T12:00:00.000Z"
      },
      "cycle_number": 2,
      "cycle_policies": {
        "normal_max_hours": 100
      },
      "telescope_capabilities": {
        "Low": "AA2",
        "Mid": "AA2"
      }
    }
  }
  }

Semantic Validation Success Response With Error for SBD-Mid input.

.. code-block:: json

    {
      "result_data": [
        "Invalid input for freq_min",
        "Invalid input for freq_max",
        "freq_min should be less than freq_max",
        "frequency_slice_id did not match fsp_id"
      ],
      "result_status": "failed",
      "result_code": 422
    }


* Example 5: Invalid JSON input.

  If user provide wrong interface or missed to add observing_command_input, then it will raise error.

Semantic Validation Error Response

.. code-block:: json

    {
      "result_data": "Missing field(s): body.observing_command_input",
      "result_status": "failed",
      "result_code": 422
    }

* Example 6:   'raise_semantic' and 'osd_data' both are optional parameters.
  So, if user do not pass these parameters, then API will take as default value of 'raise_semantic'
  i.e. true and osd_data fetch from latest release of osd_data.

.. code-block:: json

   {
    "interface":"https://schema.skao.int/ska-oso-pdm-sbd/0.1",
    "observing_command_input":{
    "interface": "https://schema.skao.int/ska-oso-pdm-sbd/0.1",
    "sbd_id": "sbi-mvp01-20200325-00001",
    "telescope": "ska_mid",
    "metadata": {
      "version": 1,
      "created_by": "Liz Bartlett",
      "created_on": "2022-03-28T15:43:53.971548+00:00",
      "last_modified_on": "2022-03-28T15:43:53.971548+00:00",
      "last_modified_by": "Liz Bartlett"
    },
    "activities": {
      "allocate": {
        "kind": "filesystem",
        "path": "file:///path/to/allocatescript.py",
        "function_args": {
          "init": {
            "args": [
              "posarg1",
              "posarg2"
            ],
            "kwargs": {
              "argname": "argval"
            }
          },
          "main": {
            "args": [
              "posarg1",
              "posarg2"
            ],
            "kwargs": {
              "argname": "argval"
            }
          }
        }
      },
      "observe": {
        "kind": "git",
        "path": "git://relative/path/to/scriptinsiderepo.py",
        "repo": "https://gitlab.com/script_repo/operational_scripts",
        "branch": "main",
        "function_args": {
          "init": {
            "args": [
              "posarg1",
              "posarg2"
            ],
            "kwargs": {
              "argname": "argval"
            }
          },
          "main": {
            "args": [
              "posarg1",
              "posarg2"
            ],
            "kwargs": {
              "argname": "argval"
            }
          }
        }
      }
    },
    "scan_definitions": [
      {
        "scan_definition_id": "calibrator scan",
        "scan_duration": 60000,
        "target": "Polaris Australis",
        "dish_configuration": "dish config 123",
        "scan_type": "calibration_B",
        "csp_configuration": "csp config 123"
      },
      {
        "scan_duration": 60000,
        "target": "M83",
        "dish_configuration": "dish config 123",
        "scan_type": "science_A",
        "scan_definition_id": "science scan",
        "csp_configuration": "csp config 123"
      }
    ],
    "scan_sequence": [
      "calibrator scan",
      "science scan",
      "science scan",
      "calibrator scan"
    ],
    "targets": [
      {
        "target_id": "Polaris Australis",
        "pointing_pattern": {
          "active": "FivePointParameters",
          "parameters": [
            {
              "kind": "FivePointParameters",
              "offset_arcsec": 5.0
            },
            {
              "kind": "RasterParameters",
              "row_length_arcsec": 1.23,
              "row_offset_arcsec": 4.56,
              "n_rows": 2,
              "pa": 7.89,
              "unidirectional": true
            },
            {
              "kind": "StarRasterParameters",
              "row_length_arcsec": 1.23,
              "n_rows": 2,
              "row_offset_angle": 4.56,
              "unidirectional": true
            }
          ]
        },
        "reference_coordinate": {
          "kind": "equatorial",
          "ra": "21:08:47.92",
          "dec": "-88:57:22.9",
          "reference_frame": "ICRS",
          "unit": [
            "hourangle",
            "deg"
          ]
        }
      },
      {
        "target_id": "M83",
        "pointing_pattern": {
          "active": "SinglePointParameters",
          "parameters": [
            {
              "kind": "SinglePointParameters",
              "offset_x_arcsec": 0.0,
              "offset_y_arcsec": 0.0
            }
          ]
        },
        "reference_coordinate": {
          "kind": "equatorial",
          "ra": "13:37:00.919",
          "dec": "-29:51:56.74",
          "reference_frame": "ICRS",
          "unit": [
            "hourangle",
            "deg"
          ]
        }
      }
    ],
    "sdp_configuration": {
      "execution_block": {
        "eb_id": "eb-mvp01-20200325-00001",
        "max_length": 100.0,
        "context": {
          "foo": "bar",
          "baz": 123
        },
        "beams": [
          {
            "beam_id": "vis0",
            "function": "visibilities"

          }
        ],
        "scan_types": [
          {
            "scan_type_id": ".default",
            "beams": [
              {
                "beam_id": "vis0",
                "channels_id": "vis_channels",
                "polarisations_id": "all"
              },
              {
                "beam_id": "pss1",
                "field_id": "M83",
                "channels_id": "pulsar_channels",
                "polarisations_id": "all"
              },
              {
                "beam_id": "pss2",
                "field_id": "Polaris Australis",
                "channels_id": "pulsar_channels",
                "polarisations_id": "all"
              },
              {
                "beam_id": "pst1",
                "field_id": "M83",
                "channels_id": "pulsar_channels",
                "polarisations_id": "all"
              },
              {
                "beam_id": "pst2",
                "field_id": "Polaris Australis",
                "channels_id": "pulsar_channels",
                "polarisations_id": "all"
              },
              {
                "beam_id": "vlbi",
                "field_id": "Polaris Australis",
                "channels_id": "vlbi_channels",
                "polarisations_id": "all"
              }
            ]
          },
          {
            "scan_type_id": ".default",
            "derive_from": ".default",
            "beams": [
              {
                "beam_id": "vis0",
                "field_id": "M83"
              }
            ]
          }
        ],
        "channels": [
          {
            "channels_id": "vis_channels",
            "spectral_windows": [
              {
                "spectral_window_id": "fsp_1_channels",
                "count": 14880,
                "start": 0,
                "stride": 2,
                "freq_min": 350000000,
                "freq_max": 368000000,
                "link_map": [
                  [
                    0,
                    0
                  ],
                  [
                    200,
                    1
                  ],
                  [
                    744,
                    2
                  ],
                  [
                    944,
                    3
                  ]
                ]
              }
            ]
          },
          {
            "channels_id": "pulsar_channels",
            "spectral_windows": [
              {
                "spectral_window_id": "pulsar_fsp_channels",
                "count": 14880,
                "start": 0,
                "freq_min": 350000000,
                "freq_max": 368000000
              }
            ]
          }
        ],
        "polarisations": [
          {
            "polarisations_id": "all",
            "corr_type": [
              "XX",
              "XY",
              "YY",
              "YX"
            ]
          }
        ]
      },
      "processing_blocks": [
        {
          "pb_id": "pb-mvp01-20200325-00001",
          "sbi_ids": [
            "sbi-mvp01-20200325-00001"
          ],
          "script": {
            "version": "0.1.0",
            "name": "vis_receive",
            "kind": "realtime"
          },
          "parameters": {}
        },
        {
          "pb_id": "pb-mvp01-20200325-00002",
          "sbi_ids": [
            "sbi-mvp01-20200325-00001"
          ],
          "script": {
            "version": "0.1.0",
            "name": "test_realtime",
            "kind": "realtime"
          },
          "parameters": {}
        },
        {
          "pb_id": "pb-mvp01-20200325-00003",
          "sbi_ids": [
            "sbi-mvp01-20200325-00001"
          ],
          "script": {
            "version": "0.1.0",
            "name": "ical",
            "kind": "batch"
          },
          "parameters": {},
          "dependencies": [
            {
              "pb_id": "pb-mvp01-20200325-00001",
              "kind": [
                "visibilities"
              ]
            }
          ]
        },
        {
          "pb_id": "pb-mvp01-20200325-00004",
          "sbi_ids": [
            "sbi-mvp01-20200325-00001"
          ],
          "script": {
            "version": "0.1.0",
            "name": "dpreb",
            "kind": "batch"
          },
          "parameters": {},
          "dependencies": [
            {
              "pb_id": "pb-mvp01-20200325-00003",
              "kind": [
                "calibration"
              ]
            }
          ]
        }
      ],
      "resources": {
        "csp_links": [
          1,
          2,
          3,
          4
        ],
        "receptors": [
          "0001",
          "0002"
        ],
        "receive_nodes": 10
      }
    },
    "csp_configurations": [
      {
        "config_id": "csp config 123",
        "subarray": {
          "subarray_name": "science period 23"
        },
        "common": {
          "subarray_id": 1,
          "band_5_tuning": [
            5.85,
            7.25
          ]
        },
        "cbf": {
          "fsp": [
            {
              "fsp_id": 1,
              "function_mode": "CORR",
              "frequency_slice_id": 1,
              "integration_factor": 1,
              "zoom_factor": 0,
              "channel_averaging_map": [
                [
                  0,
                  2
                ],
                [
                  744,
                  0
                ]
              ],
              "channel_offset": 0,
              "output_link_map": [
                [
                  0,
                  0
                ],
                [
                  200,
                  1
                ]
              ]
            },
            {
              "fsp_id": 2,
              "function_mode": "CORR",
              "frequency_slice_id": 2,
              "integration_factor": 1,
              "zoom_factor": 1,
              "zoom_window_tuning": 650000
            }
          ]
        }
      }
    ],
    "dish_allocations": {
      "receptor_ids": [
        "0001",
        "0002"
      ]
    },
    "dish_configurations": [
      {
        "dish_configuration_id": "dish config 123",
        "receiver_band": "1"
      }
    ]
  }}

Semantic Validation Success Response for SBD-Mid input.

.. code-block:: json

     {
        "result_data": "JSON is semantically valid",
        "result_status": "success",
        "result_code": 200,
    }

* Example 7: Missing key observing_command_input.

.. code-block:: json

  {
    "interface": "https://schema.skao.int/ska-tmc-assignresources/2.1",
    "raise_semantic": true,
    "sources": "car:ost/ska-ost-osd?{OSD_MAJOR_VERSION}#tmdata"
  }

Getting error as observing_command_input is required field

.. code-block:: json

  {
  "result_data": "Missing field(s): body.observing_command_input",
  "result_status": "failed",
  "result_code": 422
  }
