"""
OSD REST server entry point.
"""
import logging

from flask_cors import CORS
from gunicorn import glogging
from ska_ser_logging import configure_logging, get_default_formatter

from ska_ost_osd.rest import init_app

app = init_app()
CORS(app)  #


class UniformLogger(glogging.Logger):
    def setup(self, cfg):
        # override the configuration but inherit gunicorn logging level
        super().setup(cfg)
        configure_logging(level=self.loglevel)

        # Override gunicorn format with SKA.
        self._set_handler(self.error_log, cfg.errorlog, get_default_formatter())


if __name__ == "__main__":
    app.run(host="0.0.0.0")
else:
    # presume being run from gunicorn
    # use gunicorn logging level for app and module loggers
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.setLevel(gunicorn_logger.level)
    logger = logging.getLogger("ska_ost_osd")
    logger.setLevel(gunicorn_logger.level)
