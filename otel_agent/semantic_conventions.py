"""
Official CNCF OpenTelemetry Generative AI (GenAI) Semantic Conventions.
Aligned with open-telemetry/semantic-conventions-genai (2026 specification).
"""

class GenAISemanticAttributes:
    # Operation & System
    GEN_AI_SYSTEM = "gen_ai.system"  # e.g., "anthropic", "openai", "custom_swarm"
    GEN_AI_OPERATION_NAME = "gen_ai.operation.name"  # e.g., "agent.turn", "agent.reasoning", "tool.execute"
    
    # Request & Model
    GEN_AI_REQUEST_MODEL = "gen_ai.request.model"
    GEN_AI_RESPONSE_MODEL = "gen_ai.response.model"
    GEN_AI_REQUEST_TEMPERATURE = "gen_ai.request.temperature"
    GEN_AI_REQUEST_MAX_TOKENS = "gen_ai.request.max_tokens"
    
    # Token Usage & Metrics
    GEN_AI_USAGE_INPUT_TOKENS = "gen_ai.usage.input_tokens"
    GEN_AI_USAGE_OUTPUT_TOKENS = "gen_ai.usage.output_tokens"
    GEN_AI_USAGE_TOTAL_TOKENS = "gen_ai.usage.total_tokens"
    GEN_AI_USAGE_COST_USD = "gen_ai.usage.cost_usd"
    
    # Agent & Swarm Hierarchy
    GEN_AI_AGENT_ID = "gen_ai.agent.id"
    GEN_AI_AGENT_NAME = "gen_ai.agent.name"
    GEN_AI_AGENT_ROLE = "gen_ai.agent.role"
    GEN_AI_AGENT_PARENT_ID = "gen_ai.agent.parent_id"
    GEN_AI_AGENT_TURN_INDEX = "gen_ai.agent.turn_index"
    
    # Tool Execution & Model Context Protocol (MCP)
    GEN_AI_TOOL_NAME = "gen_ai.tool.name"
    GEN_AI_TOOL_TYPE = "gen_ai.tool.type"  # e.g., "mcp", "openapi", "custom"
    GEN_AI_TOOL_SERVER = "gen_ai.tool.server"  # e.g., "github-mcp", "postgres-mcp"
    GEN_AI_TOOL_STATUS = "gen_ai.tool.status"  # "success", "error", "rate_limited"
    
    # Memory & Context Operations
    GEN_AI_MEMORY_OPERATION = "gen_ai.memory.operation"  # "read", "write", "compact"
    GEN_AI_MEMORY_HIT = "gen_ai.memory.hit"  # bool
