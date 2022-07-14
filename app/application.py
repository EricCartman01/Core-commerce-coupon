from importlib import metadata
from pathlib import Path

from ddtrace import config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi_pagination import add_pagination

from app.api.helpers.handler import register_exception_handlers
from app.api.helpers.middlewares import LogCorrelationMiddleware
from app.api.router import api_router
from app.enums import Environment
from app.lifetime import shutdown, startup
from app.settings import settings

from .telemetry import DatadogExporter, Telemetry

APP_ROOT = Path(__file__).parent


def get_app() -> FastAPI:
    """
    Get FastAPI application.

    This is the main constructor of an application.

    :return: application.
    """

    # Override service name
    config.fastapi["service_name"] = str(settings.service_name)

    # Telemetry
    if Environment.is_valid():
        Telemetry.init()
        Telemetry.configure_exporter(DatadogExporter())

    app = FastAPI(
        title="app",
        description="Fastapi for coupon",
        version=metadata.version("app"),
        docs_url=None,
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )

    app.add_middleware(LogCorrelationMiddleware)
    if settings.backend_cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                str(origin) for origin in settings.backend_cors_origins
            ],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.on_event("startup")(startup(app))
    app.on_event("shutdown")(shutdown(app))

    app.include_router(router=api_router)
    app.mount(
        "/static",
        StaticFiles(directory=APP_ROOT / "static"),
        name="static",
    )
    add_pagination(app)
    register_exception_handlers(app)
    return app
