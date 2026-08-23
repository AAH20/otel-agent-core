from otel_agent import ContextPropagator, W3CTraceContext


def test_w3c_traceparent_serialization():
    ctx = W3CTraceContext()
    traceparent = ctx.traceparent
    assert traceparent.startswith("00-")
    assert len(traceparent.split("-")) == 4

    # Extract back
    recovered = W3CTraceContext.from_traceparent(traceparent)
    assert recovered is not None
    assert recovered.trace_id == ctx.trace_id
    assert recovered.span_id == ctx.span_id


def test_mcp_jsonrpc_meta_injection():
    ctx = W3CTraceContext()
    mcp_params = {"uri": "file:///workspace/app.py"}

    # Inject
    ContextPropagator.inject_to_mcp_params(ctx, mcp_params)
    assert "_meta" in mcp_params
    assert "traceparent" in mcp_params["_meta"]

    # Extract
    extracted = ContextPropagator.extract_from_mcp_params(mcp_params)
    assert extracted.trace_id == ctx.trace_id
    assert extracted.span_id == ctx.span_id
