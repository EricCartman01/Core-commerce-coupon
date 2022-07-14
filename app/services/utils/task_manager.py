from typing import Callable

from app.enums import TaskStatus
from app.models.task import Task
from app.repository.task import TaskRepository


async def task_wrapper(func: Callable, task_id: str, *args):
    """Run a python function in background and update task status and result
    :param func: python function that will be running in the background.
    :param task_id: id of a task object.
    :param *args: func arguments.
    """

    db_session = args[1]
    task_repository = TaskRepository(db_session)

    await task_repository.update_status(
        task_id=task_id,
        status=TaskStatus.IN_PROGRESS,
    )

    result = await func(*args)

    await task_repository.update(
        query_filter=(Task.id == task_id),
        data_to_update={
            "result": result,
            "status": TaskStatus.COMPLETED,
        },
    )
