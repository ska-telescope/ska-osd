"""
The flask_oda module contains code used to interface Flask applications with
the ODA.
"""
import logging
import os

LOGGER = logging.getLogger(__name__)

BACKEND_VAR = "ODA_BACKEND_TYPE"


class FlaskOSD(object):
    """
    FlaskODA is asmall Flask extension that makes the ODA backend available to
    Flask apps.

    This extension present two properties that can be used by Flask code to access
    the ODA. The extension should ensure that the correct scope is used; that is,
    one unique repository per Flask app and a unique UnitOfWork per HTTP request.

    The backend type is set by the ODA_BACKEND_TYPE environment variable.
    """

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """
        Initialise ODA Flask extension.
        """
        app.config[BACKEND_VAR] = os.environ.get(
            BACKEND_VAR, default=app.config.setdefault(BACKEND_VAR, "memory")
        )
        app.extensions["osd"] = self
