"""
High-Throughput Asynchronous OTLP Exporter (Standard JSON / gRPC simulation).
Formats telemetry into CNCF OpenTelemetry Protocol (OTLP/HTTP & OTLP/gRPC).
"""

import json
from typing import Any, Dict, List
from otel_agent.ring_buffer import LockFreeSpanBuffer, SpanRecord


class OTLPJsonExporter:
    def __init__(self, endpoint: str = "http://localhost:4318/v1/traces"):
        self.endpoint = endpoint

    def format_otlp_payload(self, spans: List[SpanRecord]) -> Dict[str, Any]:
        """Converts internal SpanRecords into official CNCF OTLP v1 ResourceSpans structure."""
        scope_spans = []
        for span in spans:
            attributes = [{"key": k, "value": {"stringValue": str(v)}} for k, v in span.attributes.items()]
            events = [
                {
                    "timeUnixNano": str(e["time_ns"]),
                    "name": e["name"],
                    "attributes": [{"key": k, "value": {"stringValue": str(v)}} for k, v in e.get("attributes", {}).items()],
                }
                for e in span.events
            ]
            
            otlp_span = {
                "traceId": span.trace_id,
                "spanId": span.span_id,
                "parentSpanId": span.parent_span_id or "",
                "name": span.name,
                "kind": 1,  # SPAN_KIND_INTERNAL
                "startTimeUnixNano": str(span.start_time_ns),
                "endTimeUnixNano": str(span.end_time_ns or span.start_time_ns),
                "attributes": attributes,
                "events": events,
                "status": {"code": 1 if span.status_code == "OK" else 2},
            }
            scope_spans.append(otlp_span)

        return {
            "resourceSpans": [
                {
                    "resource": {
                        "attributes": [
                            {"key": "service.name", "value": {"stringValue": "otel-agent-core"}},
                            {"key": "telemetry.sdk.language", "value": {"stringValue": "python"}},
                        ]
                    },
                    "scopeSpans": [{"scope": {"name": "otel_agent.tracer", "version": "0.1.0"}, "spans": scope_spans}],
                }
            ]
        }

    def export_batch(self, buffer: LockFreeSpanBuffer, batch_size: int = 100) -> Dict[str, Any]:
        spans = buffer.drain(batch_size)
        return self.format_otlp_payload(spans)
