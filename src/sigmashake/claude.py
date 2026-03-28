"""Claude Agent SDK integration -- expose SigmaShake as MCP tools for Claude Code."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from claude_agent_sdk import (
    tool,
    create_sdk_mcp_server,
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AgentDefinition,
)

from .client import SigmaShake


def _json_result(data: Any) -> Dict[str, Any]:
    """Wrap a result into MCP tool response format."""
    if hasattr(data, "model_dump"):
        text = json.dumps(data.model_dump(), default=str)
    elif isinstance(data, list) and data and hasattr(data[0], "model_dump"):
        text = json.dumps([d.model_dump() for d in data], default=str)
    elif isinstance(data, (dict, list)):
        text = json.dumps(data, default=str)
    else:
        text = str(data)
    return {"content": [{"type": "text", "text": text}]}


def create_tools(client: SigmaShake) -> list:
    """Create Claude Agent SDK MCP tools backed by a SigmaShake client.

    Args:
        client: An initialized SigmaShake client instance.

    Returns:
        List of tool functions for use with ``create_sdk_mcp_server``.
    """

    @tool(
        "sigmashake_search_documents",
        "Search documents in the SigmaShake platform",
        {"query": str, "limit": int, "offset": int},
    )
    async def search_documents(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.documents.search(
            query=args["query"],
            limit=args.get("limit", 10),
            offset=args.get("offset", 0),
        )
        return _json_result(result)

    @tool(
        "sigmashake_query_db",
        "Query a SigmaShake database table with optional filters",
        {
            "table_name": str,
            "filters": list,
            "columns": list,
            "limit": int,
        },
    )
    async def query_db(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.db.query(
            table_name=args["table_name"],
            filters=args.get("filters"),
            columns=args.get("columns"),
            limit=args.get("limit"),
        )
        return _json_result(result)

    @tool(
        "sigmashake_vector_search",
        "Perform vector similarity search on a SigmaShake database table",
        {
            "table_name": str,
            "column": str,
            "vector": list,
            "top_k": int,
        },
    )
    async def vector_search(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.db.vector_search(
            table_name=args["table_name"],
            column=args["column"],
            vector=args["vector"],
            top_k=args.get("top_k", 10),
        )
        return _json_result(result)

    @tool(
        "sigmashake_store_memory",
        "Store a key-value memory entry for an agent",
        {"agent_id": str, "key": str, "value": str, "tags": list},
    )
    async def store_memory(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.memory.store(
            agent_id=args["agent_id"],
            key=args["key"],
            value=args["value"],
            tags=args.get("tags"),
        )
        return _json_result(result)

    @tool(
        "sigmashake_recall_memory",
        "Search agent memory by semantic query",
        {"agent_id": str, "query": str},
    )
    async def recall_memory(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.memory.recall(
            agent_id=args["agent_id"],
            query=args["query"],
        )
        return _json_result(result)

    @tool(
        "sigmashake_get_memory",
        "Get a specific memory entry by key",
        {"agent_id": str, "key": str},
    )
    async def get_memory(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.memory.get(
            agent_id=args["agent_id"],
            key=args["key"],
        )
        return _json_result(result)

    @tool(
        "sigmashake_delete_memory",
        "Delete a memory entry by key",
        {"agent_id": str, "key": str},
    )
    async def delete_memory(args: Dict[str, Any]) -> Dict[str, Any]:
        client.memory.delete(agent_id=args["agent_id"], key=args["key"])
        return {"content": [{"type": "text", "text": "deleted"}]}

    @tool(
        "sigmashake_list_alerts",
        "List security alerts from the SigmaShake SOC",
        {"status": str, "severity": str, "limit": int},
    )
    async def list_alerts(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.soc.list_alerts(
            status=args.get("status"),
            severity=args.get("severity"),
            limit=args.get("limit", 100),
        )
        return _json_result(result)

    @tool(
        "sigmashake_get_timeline",
        "Get the event timeline for a session",
        {"session_id": str},
    )
    async def get_timeline(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.soc.get_timeline(session_id=args["session_id"])
        return _json_result(result)

    @tool(
        "sigmashake_shield_scan",
        "Scan an operation through the SigmaShake security shield",
        {"agent_id": str, "session_id": str, "operation": dict},
    )
    async def shield_scan(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.shield.scan(
            agent_id=args["agent_id"],
            session_id=args["session_id"],
            operation=args["operation"],
        )
        return _json_result(result)

    @tool(
        "sigmashake_pipeline_status",
        "Get the current SigmaShake pipeline status and health",
        {},
    )
    async def pipeline_status(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.pulse.get_status()
        return _json_result(result)

    @tool(
        "sigmashake_pipeline_metrics",
        "Get aggregated pipeline metrics for a time range",
        {"from_ts": str, "to_ts": str},
    )
    async def pipeline_metrics(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.pulse.get_metrics(
            from_ts=args.get("from_ts"),
            to_ts=args.get("to_ts"),
        )
        return _json_result(result)

    @tool(
        "sigmashake_bottlenecks",
        "Get detected pipeline bottlenecks ranked by severity",
        {"min_score": float, "limit": int},
    )
    async def bottlenecks(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.pulse.get_bottlenecks(
            min_score=args.get("min_score"),
            limit=args.get("limit"),
        )
        return _json_result(result)

    @tool(
        "sigmashake_ai_brief",
        "Get an AI-optimized summary of current pipeline state",
        {},
    )
    async def ai_brief(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.pulse.get_ai_brief()
        return _json_result(result)

    @tool(
        "sigmashake_list_agents",
        "List registered agents",
        {"limit": int, "offset": int},
    )
    async def list_agents(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.agents.list(
            limit=args.get("limit", 100),
            offset=args.get("offset", 0),
        )
        return _json_result(result)

    return [
        search_documents,
        query_db,
        vector_search,
        store_memory,
        recall_memory,
        get_memory,
        delete_memory,
        list_alerts,
        get_timeline,
        shield_scan,
        pipeline_status,
        pipeline_metrics,
        bottlenecks,
        ai_brief,
        list_agents,
    ]


def create_mcp_server(
    client: SigmaShake,
    *,
    name: str = "sigmashake",
) -> Dict[str, Any]:
    """Create an MCP server exposing SigmaShake tools for the Claude Agent SDK.

    Usage with ``ClaudeSDKClient``::

        import sigmashake
        from sigmashake.claude import create_mcp_server

        ss = sigmashake.SigmaShake(api_key="sk-...")
        server = create_mcp_server(ss)

        async with ClaudeSDKClient(options=ClaudeAgentOptions(
            mcp_servers={"sigmashake": server}
        )) as agent:
            await agent.query("Check pipeline status and list recent alerts")
            async for message in agent.receive_response():
                ...

    Usage with ``query()``::

        from sigmashake.claude import create_mcp_server, query_with_sigmashake

        ss = sigmashake.SigmaShake(api_key="sk-...")
        async for message in query_with_sigmashake(
            ss, prompt="What are the current bottlenecks?"
        ):
            ...

    Args:
        client: An initialized SigmaShake client.
        name: MCP server name (default: ``"sigmashake"``).

    Returns:
        An SDK MCP server dict for use with ``ClaudeAgentOptions.mcp_servers``.
    """
    tools = create_tools(client)
    return create_sdk_mcp_server(name, tools=tools)


async def query_with_sigmashake(
    client: SigmaShake,
    *,
    prompt: str,
    allowed_tools: Optional[List[str]] = None,
    system_prompt: Optional[str] = None,
    max_turns: Optional[int] = None,
    permission_mode: str = "default",
    extra_mcp_servers: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
):
    """Run a Claude Code agent with SigmaShake tools available.

    Convenience wrapper that creates the MCP server and calls ``query()``.

    Usage::

        import sigmashake
        from sigmashake.claude import query_with_sigmashake
        from claude_agent_sdk import ResultMessage

        ss = sigmashake.SigmaShake(api_key="sk-...")
        async for message in query_with_sigmashake(
            ss,
            prompt="Show me critical alerts and pipeline bottlenecks",
            allowed_tools=["Read", "Glob"],
        ):
            if isinstance(message, ResultMessage):
                print(message.result)

    Args:
        client: An initialized SigmaShake client.
        prompt: The task prompt for the agent.
        allowed_tools: Additional built-in tools to allow (e.g., ``["Read", "Glob"]``).
        system_prompt: Optional system prompt override.
        max_turns: Maximum agent turns.
        permission_mode: Permission mode (default: ``"default"``).
        extra_mcp_servers: Additional MCP servers to include.
        **kwargs: Passed to ``ClaudeAgentOptions``.
    """
    from claude_agent_sdk import query as sdk_query, ClaudeAgentOptions

    server = create_mcp_server(client)
    mcp_servers = {"sigmashake": server}
    if extra_mcp_servers:
        mcp_servers.update(extra_mcp_servers)

    options = ClaudeAgentOptions(
        allowed_tools=allowed_tools or [],
        mcp_servers=mcp_servers,
        permission_mode=permission_mode,
        **kwargs,
    )
    if system_prompt is not None:
        options.system_prompt = system_prompt
    if max_turns is not None:
        options.max_turns = max_turns

    async for message in sdk_query(prompt=prompt, options=options):
        yield message
