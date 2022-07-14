from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db_session
from app.enums import TaskStatus
from app.models.task import Task
from app.repository.base import BaseRepository


class TaskRepository(BaseRepository):
    """Class for accessing model table."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Task)
        self.session = session

    async def update_status(self, task_id: str, status: TaskStatus) -> int:
        """
        Update Task model by task_id.

        :param task_id: criteria of model to update.
        :param status: new status to update the model.

        :returns: count of rows to updated or -1 if error.

        :raises NoResultFound: 404 - Task not found
        :raises AssertionError: 404 - Task not found
        """
        rowcount = await self.update(
            query_filter=(Task.id == task_id),
            data_to_update={"status": status},
        )

        return rowcount

    async def update_result(self, task_id: str, result: str) -> int:
        """
        Update Task model by task_id.

        :param task_id: criteria of model to update.
        :param result: new status to update the model.

        :returns: count of rows to updated or -1 if error.

        :raises NoResultFound: 404 - Task not found
        :raises AssertionError: 404 - Task not found
        """
        rowcount = await self.update(
            query_filter=(Task.id == task_id),
            data_to_update={"result": result},
        )

        return rowcount
