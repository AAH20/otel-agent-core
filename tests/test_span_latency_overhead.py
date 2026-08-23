import time
from otel_agent import AgentTracer, LockFreeSpanBuffer


def test_sub_microsecond_span_creation():
    buffer = LockFreeSpanBuffer(capacity=50_000)
    tracer = AgentTracer(buffer=buffer)

    iterations = 5_000
    start = time.perf_counter()

    for i in range(iterations):
        with tracer.start_span(f"BenchmarkSpan_{i}", attributes={"index": i}):
            pass

    elapsed = time.perf_counter() - start
    avg_per_span_ms = (elapsed / iterations) * 1000.0

    print(f"\n[BENCHMARK] Average span creation & buffer latency: {avg_per_span_ms:.5f} ms")
    assert avg_per_span_ms < 0.05, f"Span overhead too high: {avg_per_span_ms} ms"
    assert len(buffer) == iterations
