import logging

from fastapi import FastAPI
from opentelemetry import _logs, trace
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.metrics import get_meter_provider, set_meter_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


class OTELHandler:
    def __init__(self, app: FastAPI):
        self.app = app
        self.resource = Resource(attributes={SERVICE_NAME: "arcade-actor"})

        self._init_tracer()
        self._init_metrics()
        self._init_logging()

        FastAPIInstrumentor().instrument_app(app)

    def _init_tracer(self):
        tracer_provider = TracerProvider(resource=self.resource)
        trace.set_tracer_provider(tracer_provider)

        # Create an OTLP exporter
        otlp_span_exporter = OTLPSpanExporter()

        # Create a batch span processor and add the exporter
        span_processor = BatchSpanProcessor(otlp_span_exporter)
        tracer_provider.add_span_processor(span_processor)

    def _init_metrics(self):
        otlp_metric_exporter = OTLPMetricExporter()

        reader = PeriodicExportingMetricReader(otlp_metric_exporter)

        provider = MeterProvider(metric_readers=[reader], resource=self.resource)

        set_meter_provider(provider)

        self.get_meter().create_counter("tool_call_request_count")

    def get_meter(self):
        return get_meter_provider().get_meter(__name__)

    def _init_logging(self):
        otlp_log_exporter = OTLPLogExporter()

        log_provider = LoggerProvider(resource=self.resource)
        _logs.set_logger_provider(log_provider)

        # Create a batch span processor and add the exporter
        log_processor = BatchLogRecordProcessor(otlp_log_exporter)
        log_provider.add_log_record_processor(log_processor)

        handler = LoggingHandler(level=logging.NOTSET, logger_provider=log_provider)
        logging.getLogger().addHandler(handler)
