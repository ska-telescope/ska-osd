"""
  created file to maintain televalidation constant
"""


# flake8: noqa E501

MID_VALIDATION_CONSTANT_JSON_FILE_PATH = (
    "instrument/ska1_mid/validation/mid-validation-constants.json"
)
LOW_VALIDATION_CONSTANT_JSON_FILE_PATH = (
    "instrument/ska1_low/validation/low-validation-constants.json"
)
SBD_VALIDATION_CONSTANT_JSON_FILE_PATH = (
    "instrument/scheduling-block/validation/sbd-validation-constants.json"
)
MID_LAYOUT_CONSTANT_JSON_FILE_PATH = "instrument/ska1_mid/layout/mid-layout.json"
LOW_LAYOUT_CONSTANT_JSON_FILE_PATH = "instrument/ska1_low/layout/low-layout.json"

SKA_LOW_TELESCOPE = "low"
SKA_MID_TELESCOPE = "mid"
SKA_SBD = "sbd"

CAR_TELMODEL_SOURCE = ("car:ost/ska-ost-osd?main#tmdata",)

INTERFACE_PATTERN = r"^https://schema\.skao\.int/[a-zA-Z-]+/\d+\.\d+$"
