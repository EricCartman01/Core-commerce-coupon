from importlib import metadata

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

import app.api.healthcheck.checkers.database as database
from app.db.dependencies import get_db_session
from app.settings import settings

router = APIRouter()


@router.get("/", include_in_schema=False)
async def get_app():
    return [{"app": settings.service_name, "version": metadata.version("app")}]


@router.get("/health")
async def get_health(session: AsyncSession = Depends(get_db_session)):
    checkers = [
        database.Checker(session),
    ]

    return await healthcheck(checkers)


async def healthcheck(checkers=[]):
    checks = []
    for checker in checkers:
        checks.append(await checker.check())

    status = True
    for check in checks:
        if check["status"] is False:
            status = False
    return {"name": settings.service_name, "status": status, "checks": checks}
