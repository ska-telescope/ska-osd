"""This module allows custom exceptions for semantic validation"""


class SchematicValidationError(ValueError):
    """Class to accept the various error messages from validator module"""

    def __init__(self, message="Undefined error", **_):
        self.message = message
        super().__init__(self.message)


class SchemanticValidationKeyError(KeyError):
    """class to raise invalid input key for schemantic validation"""

    # flake8: noqa E501
    def __init__(
        self,
        message="It seems there is an issue with Validator JSON schema file, Please check and correct the JSON keys and try again.",
        **_,
    ):
        self.message = message
        super().__init__(self.message)
