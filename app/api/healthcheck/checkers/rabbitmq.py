import time

import pika

from .base import Base


class Checker(Base):
    def __init__(
        self, url="amqp://guest:guest@localhost:5672/", name="RabbitMQ"
    ):
        super().__init__(name)
        self.url = url
        self.name = name

    async def check(self, session=None):
        start = time.time()
        status = False
        try:
            parameters = pika.URLParameters(self.url)
            connection = pika.BlockingConnection(parameters)
            if connection.is_open:
                status = True
                connection.close()
        except Exception:
            status = False

        time_passed = time.time() - start
        return {"name": self.name, "status": status, "time": time_passed}
