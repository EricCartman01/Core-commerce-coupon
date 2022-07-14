import abc
import os

from opentelemetry import trace
from opentelemetry.exporter.datadog import (
    DatadogExportSpanProcessor,
    DatadogSpanExporter,
)
from opentelemetry.exporter.datadog.propagator import DatadogFormat
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.propagate import get_global_textmap, set_global_textmap
from opentelemetry.propagators.composite import CompositeHTTPPropagator
from opentelemetry.sdk.trace import SpanProcessor, TracerProvider


class Exporter(abc.ABC):
    @staticmethod
    @abc.abstractmethod
    def get_span_processor() -> SpanProcessor:
        ...


class Instrument(abc.ABC):
    @staticmethod
    @abc.abstractmethod
    def perform_instrumentation(*args) -> None:
        ...


class Uninstrument(abc.ABC):
    @staticmethod
    @abc.abstractmethod
    def perform_uninstrument(*args) -> None:
        ...


class DatadogExporter(Exporter):
    @staticmethod
    def configure_propagator():
        global_textmap = get_global_textmap()
        if isinstance(global_textmap, CompositeHTTPPropagator) and not any(
            isinstance(p, DatadogFormat) for p in global_textmap._propagators
        ):
            set_global_textmap(
                CompositeHTTPPropagator(
                    global_textmap._propagators + [DatadogFormat()]
                )
            )
        else:
            set_global_textmap(DatadogFormat())

    @classmethod
    def get_span_processor(cls) -> SpanProcessor:
        cls.configure_propagator()

        return DatadogExportSpanProcessor(
            DatadogSpanExporter(
                agent_url=f"http://{os.environ.get('DD_AGENT_HOST')}:8126"
            )
        )


class FastAPIInstrument(Instrument, Uninstrument):
    @staticmethod
    def perform_instrumentation(app) -> None:
        FastAPIInstrumentor.instrument_app(app)

    @staticmethod
    def perform_uninstrument(app) -> None:
        FastAPIInstrumentor.uninstrument_app(app)


class AsyncPGInstrument(Instrument):
    @staticmethod
    def perform_instrumentation() -> None:
        AsyncPGInstrumentor().instrument()


class SQLAlchemyInstrument(Instrument):
    @staticmethod
    def perform_instrumentation(engine) -> None:
        SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)


class Telemetry:
    @staticmethod
    def init() -> None:
        trace.set_tracer_provider(TracerProvider())

    @staticmethod
    def configure_exporter(exporter: Exporter) -> None:
        trace.get_tracer_provider().add_span_processor(
            exporter.get_span_processor()
        )

    @staticmethod
    def instrument(instrument: Instrument, *args) -> None:
        instrument.perform_instrumentation(*args)

    @staticmethod
    def uninstrument(uninstrument: Uninstrument, *args) -> None:
        uninstrument.perform_uninstrument(*args)
