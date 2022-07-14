from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.sql.expression import select

from app.enums import TaskStatus
from app.models.task import Task
from app.repository.task import TaskRepository
from app.services.utils.task_manager import task_wrapper


@pytest.mark.asyncio
async def test_create_task(db_session):
    # GIVEN
    task_data = {
        "result": "TEST",
        "data": '{ "message" : "ok"}',
    }

    # WHEN
    task = Task(**task_data)
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    # THEN
    assert task.status in TaskStatus.CREATED
    assert isinstance(task.created_at, datetime)


@pytest.mark.asyncio
async def test_update_status_task(db_session):
    # GIVEN
    repository = TaskRepository(db_session)
    task_data = {
        "result": "TEST",
        "data": {"message": "ok"},
    }
    task = Task(**task_data)
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    assert task.status in TaskStatus.CREATED

    # WHEN
    row_count = await repository.update_status(
        task.id,
        TaskStatus.IN_PROGRESS,
    )
    raw = await db_session.execute(
        select(Task).where(Task.id == task.id),
    )
    obj = raw.scalar_one()

    # THEN
    assert obj.id == task.id
    assert obj.status in TaskStatus.IN_PROGRESS
    assert obj.status == "in_progress"
    assert row_count == 1


@pytest.mark.asyncio
async def test_update_result_task(db_session):
    # GIVEN
    repository = TaskRepository(db_session)
    task_data = {
        "result": "TEST",
        "data": {"message": "ok"},
    }

    task = Task(**task_data)
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    assert task.result in "TEST"

    # WHEN
    row_count = await repository.update_result(
        task.id,
        "FINISHTEST",
    )
    raw = await db_session.execute(
        select(Task).where(Task.id == task.id),
    )
    obj = raw.scalar_one()

    # THEN
    assert obj.id == task.id
    assert obj.result == "FINISHTEST"
    assert row_count == 1
