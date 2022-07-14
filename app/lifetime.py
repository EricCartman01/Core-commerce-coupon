from asyncio import current_task
from typing import Awaitable, Callable

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_scoped_session,
    create_async_engine,
)
from sqlalchemy.orm import configure_mappers, sessionmaker

from app.enums import Environment
from app.settings import settings

from .telemetry import (
    AsyncPGInstrument,
    FastAPIInstrument,
    SQLAlchemyInstrument,
    Telemetry,
)

engine = create_async_engine(str(settings.db_url), echo=settings.db_echo)
session_factory = async_scoped_session(
    sessionmaker(
        engine,
        expire_on_commit=False,
        class_=AsyncSession,
    ),
    scopefunc=current_task,
)


def _setup_db(app: FastAPI) -> None:
    """
    Create connection to the database.
    This function creates SQLAlchemy engine instance,
    session_factory for creating sessions
    and stores them in the application's state property.
    :param app: fastAPI application.
    """

    # Instrumentation
    if Environment.is_valid():
        Telemetry.instrument(SQLAlchemyInstrument(), engine)

    app.state.db_engine = engine
    app.state.db_session_factory = session_factory
    configure_mappers()


def startup(app: FastAPI) -> Callable[[], Awaitable[None]]:
    """
    Actions to run on application startup.
    This function use fastAPI app to store data,
    such as db_engine.
    :param app: the fastAPI application.
    :return: function that actually performs actions.
    """

    async def _startup() -> None:
        _setup_db(app)

        # Instrumentation and Log correlation
        if Environment.is_valid():
            Telemetry.instrument(FastAPIInstrument(), app)
            Telemetry.instrument(AsyncPGInstrument())

    return _startup


def shutdown(app: FastAPI) -> Callable[[], Awaitable[None]]:
    """
    Actions to run on application's shutdown.
    :param app: fastAPI application.
    :return: function that actually performs actions.
    """

    async def _shutdown() -> None:
        Telemetry.uninstrument(FastAPIInstrument(), app)
        await app.state.db_engine.dispose()

    return _shutdown
