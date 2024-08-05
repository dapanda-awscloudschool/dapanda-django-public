import logging
from opentelemetry.sdk._logs import LoggingHandler

class OpenTelemetryHandler(logging.Handler):
    def __init__(self, otel_logging_handler):
        super().__init__()
        self.otel_logging_handler = otel_logging_handler

    def emit(self, record):
        self.otel_logging_handler.emit(record)
