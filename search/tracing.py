import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

def setup_tracing():
    # TracerProvider가 이미 설정되었는지 확인
    if trace.get_tracer_provider().__class__ is TracerProvider:
        # 이미 설정된 TracerProvider가 있으면 설정을 건너뜁니다.
        return

    # 환경 변수에서 엔드포인트와 서비스 이름을 가져옴
    otlp_endpoint = os.getenv('OTLP_ENDPOINT', 'opentelemetry-collector.istio-system.svc.cluster.local:4317')
    service_name = os.getenv('SERVICE_NAME', 'dapanda')

    # Resource 생성
    resource = Resource.create({
        "service.name": service_name,
        "telemetry.sdk.name": "opentelemetry",
        "telemetry.sdk.language": "python",
        "telemetry.sdk.version": "1.25.0"
    })

    # TracerProvider 설정
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)

    # OTLPSpanExporter 설정
    otlp_exporter = OTLPSpanExporter(
        endpoint=otlp_endpoint,
        insecure=True  # SSL/TLS 설정에 따라 필요에 맞게 조정
    )

    # Span Processor 추가
    span_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(span_processor)
