from loguru import logger
from opentelemetry import trace
from starlette.types import ASGIApp, Receive, Scope, Send


class LogCorrelationMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        span_local = trace.get_current_span()
        ctx = span_local.get_span_context()
        logger.configure(
            extra={
                "dd": {
                    "trace_id": str(ctx.trace_id & 0xFFFFFFFFFFFFFFFF),
                    "span_id": str(ctx.span_id),
                }
            }
        )
        await self.app(scope, receive, send)
