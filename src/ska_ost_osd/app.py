"""ska_ost_osd app.py."""

import logging
import os
from importlib.metadata import version

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from ska_ser_logging import configure_logging

from ska_ost_osd.common.error_handling import generic_exception_handler
from ska_ost_osd.osd.common.error_handling import OSDModelError
from ska_ost_osd.osd.routers.api import osd_router
from ska_ost_osd.telvalidation.common.error_handling import (
    schematic_validation_error_handler,
)
from ska_ost_osd.telvalidation.common.schematic_validation_exceptions import (
    SchematicValidationError,
)

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
    app.include_router(osd_router, prefix=API_PREFIX, tags=["OSD"])

    # Add handlers for different types of error
    app.exception_handler(OSDModelError)(generic_exception_handler)
    app.exception_handler(SchematicValidationError)(schematic_validation_error_handler)
    app.exception_handler(RequestValidationError)(generic_exception_handler)
    app.exception_handler(ResponseValidationError)(generic_exception_handler)
    app.exception_handler(ValueError)(generic_exception_handler)
    app.exception_handler(FileNotFoundError)(generic_exception_handler)
    app.exception_handler(RuntimeError)(generic_exception_handler)
    app.exception_handler(ValidationError)(generic_exception_handler)

    if not production:
        app.exception_handler(Exception)(generic_exception_handler)
    return app


main = create_app()
