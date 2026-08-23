from otel_agent import (
    AgentTracer,
    LockFreeSpanBuffer,
    OTLPJsonExporter,
    A2ZSOCTelemetryAdapter,
)


def test_multi_agent_causality_dag():
    buffer = LockFreeSpanBuffer()
    tracer = AgentTracer(buffer=buffer)

    # 1. Root Planner Agent
    with tracer.start_span("Agent:Planner", attributes={"gen_ai.agent.name": "Planner"}) as planner_scope:
        # 2. Child Coder Agent
        with tracer.start_span("Agent:Coder", attributes={"gen_ai.agent.name": "Coder"}) as coder_scope:
            # 3. Tool Execution inside Coder
            with tracer.start_span("Tool:read_file", attributes={"gen_ai.tool.name": "read_file", "gen_ai.tool.type": "mcp"}):
                pass
            with tracer.start_span("Tool:patch_file", attributes={"gen_ai.tool.name": "patch_file", "gen_ai.tool.type": "mcp"}):
                pass

        # 4. Child Tester Agent
        with tracer.start_span("Agent:Tester", attributes={"gen_ai.agent.name": "Tester"}):
            with tracer.start_span("Tool:run_pytest", attributes={"gen_ai.tool.name": "run_pytest"}):
                pass

    # Verify all 6 spans exist in buffer
    assert len(buffer) == 6
    spans = buffer.drain(10)
    assert len(spans) == 6

    # Verify all spans share the same Root Trace ID
    root_trace_id = spans[0].trace_id
    assert all(s.trace_id == root_trace_id for s in spans)

    # Verify OTLP Export
    exporter = OTLPJsonExporter()
    payload = exporter.format_otlp_payload(spans)
    assert "resourceSpans" in payload
    assert len(payload["resourceSpans"][0]["scopeSpans"][0]["spans"]) == 6

    # Verify A2Z SOC Audit Receipt
    adapter = A2ZSOCTelemetryAdapter(tenant_id="test-cluster")
    receipt = adapter.generate_audit_receipt(spans)
    assert receipt["span_count"] == 6
    assert receipt["compliance_attestation"] == "EU_AI_ACT_ART_13_55_VERIFIED"
    assert len(receipt["causality_merkle_root"]) == 64
