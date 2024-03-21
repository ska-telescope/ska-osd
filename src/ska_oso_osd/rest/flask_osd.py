"""
The flask_osd module contains code used to interface Flask applications with
the OSD.
"""
import logging
import os

LOGGER = logging.getLogger(__name__)

BACKEND_VAR = "OSD_BACKEND_TYPE"


class FlaskOSD(object):
    """
    FlaskOSD is asmall Flask extension that makes the OSD backend available to
    Flask apps.

    This extension present two properties that can be used by Flask code to access
    the OSD. The extension should ensure that the correct scope is used; that is,
    one unique repository per Flask app and a unique UnitOfWork per HTTP request.

    The backend type is set by the OSD_BACKEND_TYPE environment variable.
    """

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """
        Initialise OSD Flask extension.
        """
        app.config[BACKEND_VAR] = os.environ.get(
            BACKEND_VAR, default=app.config.setdefault(BACKEND_VAR, "memory")
        )
        app.extensions["osd"] = self
