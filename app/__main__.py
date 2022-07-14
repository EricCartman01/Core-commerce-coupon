from uvicorn import Config, Server

from app.api.helpers.logging import setup_logging
from app.settings import settings


def main() -> None:
    server = Server(
        Config(
            "app.application:get_app",
            workers=settings.workers_count,
            host=settings.host,
            port=settings.port,
            reload=settings.reload,
            factory=True,
        ),
    )
    setup_logging()
    server.run()


if __name__ == "__main__":
    main()
