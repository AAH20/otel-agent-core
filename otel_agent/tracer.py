"""
Autonomous Agent OpenTelemetry Tracer.
Provides `@trace_agent_step` and `@trace_tool_call` decorators and span lifecycle management.
"""

import contextvars
import functools
import time
from typing import Any, Callable, Dict, Optional

from otel_agent.context_propagator import ContextPropagator, W3CTraceContext
from otel_agent.ring_buffer import LockFreeSpanBuffer, SpanRecord
from otel_agent.semantic_conventions import GenAISemanticAttributes

# Context variable for active trace context across async tasks
_current_context: contextvars.ContextVar[Optional[W3CTraceContext]] = contextvars.ContextVar(
    "_current_context", default=None
)

# Global default ring buffer
global_span_buffer = LockFreeSpanBuffer()


def get_current_context() -> W3CTraceContext:
    ctx = _current_context.get()
    if ctx is None:
        ctx = W3CTraceContext()
        _current_context.set(ctx)
    return ctx


class AgentTracer:
    def __init__(self, buffer: Optional[LockFreeSpanBuffer] = None):
        self.buffer = buffer if buffer is not None else global_span_buffer

    def start_span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        parent_context: Optional[W3CTraceContext] = None,
    ) -> "SpanScope":
        parent = parent_context or get_current_context()
        child = parent.child_context()
        _current_context.set(child)

        span = SpanRecord(
            name=name,
            trace_id=child.trace_id,
            span_id=child.span_id,
            start_time_ns=time.time_ns(),
            parent_span_id=parent.span_id if parent_context or parent != child else None,
            attributes=attributes or {},
        )
        return SpanScope(span, self.buffer, parent)


class SpanScope:
    def __init__(self, span: SpanRecord, buffer: LockFreeSpanBuffer, prev_context: W3CTraceContext):
        self.span = span
        self.buffer = buffer
        self.prev_context = prev_context

    def set_attribute(self, key: str, value: Any) -> None:
        self.span.attributes[key] = value

    def set_error(self, err: Exception) -> None:
        self.span.status_code = "ERROR"
        self.span.events.append(
            {
                "name": "exception",
                "time_ns": time.time_ns(),
                "attributes": {"exception.type": type(err).__name__, "exception.message": str(err)},
            }
        )

    def __enter__(self) -> "SpanScope":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.span.end_time_ns = time.time_ns()
        if exc_val is not None:
            self.set_error(exc_val)
        self.buffer.push(self.span)
        _current_context.set(self.prev_context)


def trace_agent_step(agent_name: str, role: str = "general"):
    """Decorator to trace an autonomous agent turn or reasoning step."""
    tracer = AgentTracer()

    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            attrs = {
                GenAISemanticAttributes.GEN_AI_SYSTEM: "autonomous_agent",
                GenAISemanticAttributes.GEN_AI_OPERATION_NAME: "agent.turn",
                GenAISemanticAttributes.GEN_AI_AGENT_NAME: agent_name,
                GenAISemanticAttributes.GEN_AI_AGENT_ROLE: role,
            }
            with tracer.start_span(f"AgentStep:{agent_name}", attributes=attrs) as scope:
                result = await func(*args, **kwargs)
                return result

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            attrs = {
                GenAISemanticAttributes.GEN_AI_SYSTEM: "autonomous_agent",
                GenAISemanticAttributes.GEN_AI_OPERATION_NAME: "agent.turn",
                GenAISemanticAttributes.GEN_AI_AGENT_NAME: agent_name,
                GenAISemanticAttributes.GEN_AI_AGENT_ROLE: role,
            }
            with tracer.start_span(f"AgentStep:{agent_name}", attributes=attrs) as scope:
                return func(*args, **kwargs)

        import inspect
        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper

    return decorator


def trace_tool_call(tool_name: str, tool_type: str = "mcp", server_name: str = "local"):
    """Decorator to trace an MCP or API tool execution."""
    tracer = AgentTracer()

    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            attrs = {
                GenAISemanticAttributes.GEN_AI_OPERATION_NAME: "tool.execute",
                GenAISemanticAttributes.GEN_AI_TOOL_NAME: tool_name,
                GenAISemanticAttributes.GEN_AI_TOOL_TYPE: tool_type,
                GenAISemanticAttributes.GEN_AI_TOOL_SERVER: server_name,
            }
            with tracer.start_span(f"ToolCall:{tool_name}", attributes=attrs) as scope:
                try:
                    result = await func(*args, **kwargs)
                    scope.set_attribute(GenAISemanticAttributes.GEN_AI_TOOL_STATUS, "success")
                    return result
                except Exception as e:
                    scope.set_attribute(GenAISemanticAttributes.GEN_AI_TOOL_STATUS, "error")
                    raise e

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            attrs = {
                GenAISemanticAttributes.GEN_AI_OPERATION_NAME: "tool.execute",
                GenAISemanticAttributes.GEN_AI_TOOL_NAME: tool_name,
                GenAISemanticAttributes.GEN_AI_TOOL_TYPE: tool_type,
                GenAISemanticAttributes.GEN_AI_TOOL_SERVER: server_name,
            }
            with tracer.start_span(f"ToolCall:{tool_name}", attributes=attrs) as scope:
                try:
                    result = func(*args, **kwargs)
                    scope.set_attribute(GenAISemanticAttributes.GEN_AI_TOOL_STATUS, "success")
                    return result
                except Exception as e:
                    scope.set_attribute(GenAISemanticAttributes.GEN_AI_TOOL_STATUS, "error")
                    raise e

        import inspect
        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper

    return decorator
