"""ska_ost_osd app.py."""

import logging
import os
from importlib.metadata import version

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ska_ser_logging import configure_logging

from ska_ost_osd.common.error_handling import development_exception_handler
from ska_ost_osd.routers.osd_api import osd_router

KUBE_NAMESPACE = os.getenv("KUBE_NAMESPACE", "ska-ost-osd")
OSD_MAJOR_VERSION = version("ska-ost-osd").split(".")[0]
API_PREFIX = f"/{KUBE_NAMESPACE}/osd/api/v{OSD_MAJOR_VERSION}"

PRODUCTION = os.getenv("PRODUCTION", "false").lower() == "true"

LOGGER = logging.getLogger(__name__)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


def create_app(production=PRODUCTION) -> FastAPI:
    """Create the FastAPI application with required config."""
    LOGGER.info("Creating FastAPI app")
    configure_logging(level=LOG_LEVEL)

    app = FastAPI(openapi_url=f"{API_PREFIX}/openapi.json", docs_url=f"{API_PREFIX}/ui")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    # Assemble the constituent APIs:
    app.include_router(osd_router, prefix=API_PREFIX)

    if not production:
        app.exception_handler(Exception)(development_exception_handler)
    return app


main = create_app()
