import time

from .base import Base


class Checker(Base):
    def __init__(
        self,
        session,
        name="Postgres",
    ):
        super().__init__(name)
        self.name = name
        self.session = session

    async def check(self):
        start = time.time()
        status = False
        try:
            result = await self.session.execute("select 1=1")
            status = result.scalar_one()
        except Exception:
            status = False

        time_passed = time.time() - start
        return {"name": self.name, "status": status, "time": time_passed}
