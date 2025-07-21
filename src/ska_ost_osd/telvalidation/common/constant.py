"""Created file to maintain televalidation constant."""

# flake8: noqa E501

MID_VALIDATION_CONSTANT_JSON_FILE_PATH = (
    "instrument/ska1_mid/validation/mid-validation-constants.json"
)
LOW_VALIDATION_CONSTANT_JSON_FILE_PATH = (
    "instrument/ska1_low/validation/low-validation-constants.json"
)
MID_SBD_VALIDATION_CONSTANT_JSON_FILE_PATH = (
    "instrument/scheduling-block/validation/mid_sbd-validation-constants.json"
)
LOW_SBD_VALIDATION_CONSTANT_JSON_FILE_PATH = (
    "instrument/scheduling-block/validation/low_sbd-validation-constants.json"
)
SWAGGER_SEMANTIC_VALIDATION_JSON_FILE_PATH = "data/sample_semantic_validation.json"
MID_LAYOUT_CONSTANT_JSON_FILE_PATH = "instrument/ska1_mid/layout/mid-layout.json"
LOW_LAYOUT_CONSTANT_JSON_FILE_PATH = "instrument/ska1_low/layout/low-layout.json"

SKA_LOW_TELESCOPE = "low"
SKA_MID_TELESCOPE = "mid"
SKA_MID_SBD = "ska_mid"
SKA_LOW_SBD = "ska_low"

ASSIGN_RESOURCE = "assignresources"
CONFIGURE = "configure"

CAR_TELMODEL_SOURCE = "car:ost/ska-ost-osd?main#tmdata"

INTERFACE_PATTERN = r"^https://schema\.skao\.int/[a-zA-Z-]+/\d+\.\d+$"

SEMANTIC_VALIDATION_VALUE = 2


# validation msgs
SEMANTIC_VALIDATION_DISABLED_MSG = "Semantic Validation is currently disabled"
SEMANTICALLY_VALID_JSON_MSG = "JSON is semantically valid"
