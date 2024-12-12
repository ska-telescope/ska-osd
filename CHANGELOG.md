############
Change Log
############

All notable changes to this project will be documented in this file.
This project adheres to `Semantic Versioning <http://semver.org/>`_.

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
