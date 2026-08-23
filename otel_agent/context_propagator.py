"""
W3C TraceContext (traceparent & tracestate) Injector and Extractor.
Ensures causality across sub-agent processes, HTTP, gRPC, SSE, and stdio JSON-RPC.
"""

import os
import re
import secrets
from typing import Any, Dict, Optional, Tuple

TRACEPARENT_REGEX = re.compile(r"^00-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$")


class W3CTraceContext:
    def __init__(self, trace_id: Optional[str] = None, span_id: Optional[str] = None, sampled: bool = True):
        self.trace_id = trace_id or secrets.token_hex(16)
        self.span_id = span_id or secrets.token_hex(8)
        self.sampled = sampled

    @property
    def traceparent(self) -> str:
        flags = "01" if self.sampled else "00"
        return f"00-{self.trace_id}-{self.span_id}-{flags}"

    @classmethod
    def from_traceparent(cls, traceparent_str: str) -> Optional["W3CTraceContext"]:
        match = TRACEPARENT_REGEX.match(traceparent_str.strip())
        if not match:
            return None
        trace_id, span_id, flags = match.groups()
        sampled = flags == "01"
        return cls(trace_id=trace_id, span_id=span_id, sampled=sampled)

    def child_context(self) -> "W3CTraceContext":
        """Generates a new child context retaining the original trace_id with a fresh span_id."""
        return W3CTraceContext(
            trace_id=self.trace_id,
            span_id=secrets.token_hex(8),
            sampled=self.sampled,
        )


class ContextPropagator:
    @staticmethod
    def inject_to_headers(context: W3CTraceContext, headers: Dict[str, str]) -> Dict[str, str]:
        headers["traceparent"] = context.traceparent
        return headers

    @staticmethod
    def extract_from_headers(headers: Dict[str, str]) -> W3CTraceContext:
        traceparent = headers.get("traceparent") or headers.get("TRACEPARENT")
        if traceparent:
            extracted = W3CTraceContext.from_traceparent(traceparent)
            if extracted:
                return extracted
        return W3CTraceContext()

    @staticmethod
    def inject_to_mcp_params(context: W3CTraceContext, params: Dict[str, Any]) -> Dict[str, Any]:
        """Injects traceparent into MCP JSON-RPC meta field."""
        if "_meta" not in params:
            params["_meta"] = {}
        params["_meta"]["traceparent"] = context.traceparent
        return params

    @staticmethod
    def extract_from_mcp_params(params: Dict[str, Any]) -> W3CTraceContext:
        """Extracts traceparent from MCP JSON-RPC meta field."""
        meta = params.get("_meta", {})
        if isinstance(meta, dict) and "traceparent" in meta:
            extracted = W3CTraceContext.from_traceparent(meta["traceparent"])
            if extracted:
                return extracted
        return W3CTraceContext()
