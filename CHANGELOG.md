############
Change Log
############

All notable changes to this project will be documented in this file.
This project adheres to `Semantic Versioning <http://semver.org/>`_.

Development
***********
* NAK-1352 Refactor handling of TelModel data sources including default

4.2.2
***********
* Added band 5b to the available receivers for Mid AA0.5

4.2.1
***********
* Fix issue due to now running `make osd-pre-release`

4.2.0
***********
* Added support for `array_assembly` in `semantic_validation` API
* Updated doc strings to sphinx style format
* Refactoring of test cases
* Added support to update `openapi.json` file using make
* Add support for sub_bands in band 5b and adjusted 5b frequency range. 
* Modified rules to ensure band 5b setups are specified in the B1 frequency range.  

4.1.0
*****
* NAK-1300 Migrate tmdata files to schmea-mapped directories
* NAK-1300 Update to ska-telmodel 1.23.2 for key aliasing

4.0.0
**********
* Migrated APIs from Flask to FastAPI
* [BREAKING] Refactored folder structure
* [BREAKING] Separated OSD and TelValidation modules
* [BREAKING] Introduced a generalized response format

3.1.1
**********
* Fixed version mapping file path issue while checking cycle_id present or not.

3.1.0
**********
* Decoupled Release process of TMData from `ska-ost-osd` source code.
* Now OSD User can publish TMData automatically from OSD UI Editor.
* Introduced new APIs to automate TMData release process. 
* Updated OSD User guide.

3.0.0
**********
* [BREAKING] Added `number_dish_ids` in Mid Capabilities.
* [BREAKING] Removed `number_channel` key.
* [BREAKING] Converted `allowed_channel_count_range_min` and `allowed_channel_count_range_max` string type to list.
* [BREAKING] Added `allowed_channel_width_values` key.
* Updated Docs for Mid and Low Capabilities.
* Refactored Test cases and restructured Test folder.

2.3.1
**********
* Updated to deepdiff version 7.0.0.
* Updated to pydantic version 2.10.3

2.3.0
********
* Upgraded astropy version to 6.1 from 5.1.

2.2.1
********
* Fixed Semantic Validation error message bug.
* Fixed OSD document issue.
  - Changelog was not reflecting earlier so fixed that.
  - RTD build was failing on pipeline.

2.2.0
*******
* Added VALIDATION_STRICTNESS environment variable to enable the functionality of semantic validation to turn on/off.

2.1.0
**************
* Verify OSD version mapping behaviour along with remove hard coded error messages checks from OSD code.
* Combined osd and semantic API input validations.
* Updated the telmodel tag to 0.19.4
  - TMC-Mid Configure v4.1: Added pointing.groups to bring OSO/TMC-Mid pointing interface up to date with ADR-63 (sky coordinates), ADR-106 (tracking and mapping), and ADR-94 (holography).
  - TMC-Mid Configure v4.1: Deprecated pointing.target
  - SKB-462 resolved

2.0.1
*****
* Added CHANGELOG.rst into doc folder.
* Reverted ArgumentType of "TMData" in function "semantic_validate" and ReturnType of semantic_validate function 
  which had been changed during refactoring and causing linting issue in CDM.

2.0.0
*****
* Removed complex code and increase readability
* Fixed independance semantic validation call issue.
* Modified test cases added parameterized test cases.
* Added semantic validation for LOW SB.
* MID and Low capabilities enhancement to support validation.

1.0.3
******
* Improve API level validation for OSD API's

1.0.2
******
* Removed requirement.txt file from docs folder.

1.0.1
******
* Fixed pipeline issue after release tag for 1.0.0 version.
* Fixed RTD documentation issue.
* Fixed minor variable names.


1.0.0
******

* Decoupled and added of Semantic Validation and OSD functionalities from ska-telmodel
* The functionalities have been exposed as a service
