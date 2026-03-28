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

    @tool(
        "sigmashake_register_agent",
        "Register a new agent with the SigmaShake platform",
        {"agent_id": str, "agent_type": str, "metadata": dict},
    )
    async def register_agent(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.agents.register(
            agent_id=args["agent_id"],
            agent_type=args["agent_type"],
            metadata=args.get("metadata"),
        )
        return _json_result(result)

    @tool(
        "sigmashake_get_agent",
        "Get details of a registered agent by ID",
        {"agent_id": str},
    )
    async def get_agent(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.agents.get(agent_id=args["agent_id"])
        return _json_result(result)

    @tool(
        "sigmashake_update_agent",
        "Update an agent's metadata",
        {"agent_id": str, "metadata": dict},
    )
    async def update_agent(args: Dict[str, Any]) -> Dict[str, Any]:
        metadata = args.get("metadata", {})
        result = client.agents.update(agent_id=args["agent_id"], **metadata)
        return _json_result(result)

    # -- Shield ---------------------------------------------------------------

    @tool(
        "sigmashake_shield_register",
        "Register an agent session with the security shield",
        {"agent_id": str, "agent_type": str, "session_ttl_secs": int, "metadata": dict},
    )
    async def shield_register(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.shield.register_agent(
            agent_id=args["agent_id"],
            agent_type=args["agent_type"],
            session_ttl_secs=args.get("session_ttl_secs", 3600),
            metadata=args.get("metadata"),
        )
        return _json_result(result)

    # -- Pulse (remaining) ----------------------------------------------------

    @tool(
        "sigmashake_get_pipeline_runs",
        "List recent pipeline runs with optional time range filter",
        {"page": int, "per_page": int, "from_ts": str, "to_ts": str},
    )
    async def get_pipeline_runs(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.pulse.get_runs(
            page=args.get("page", 1),
            per_page=args.get("per_page", 20),
            from_ts=args.get("from_ts"),
            to_ts=args.get("to_ts"),
        )
        return _json_result(result)

    @tool(
        "sigmashake_get_pipeline_run",
        "Get full detail for a specific pipeline run by ID",
        {"run_id": str},
    )
    async def get_pipeline_run(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.pulse.get_run(run_id=args["run_id"])
        return _json_result(result)

    @tool(
        "sigmashake_trigger_pipeline",
        "Trigger a new pipeline run",
        {"trigger_type": str, "config": dict},
    )
    async def trigger_pipeline(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.pulse.trigger_run(
            trigger_type=args["trigger_type"],
            config=args.get("config"),
        )
        return _json_result(result)

    @tool(
        "sigmashake_push_events",
        "Ingest external events into the Pulse pipeline for correlation",
        {"events": list},
    )
    async def push_events(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.pulse.push_event(events=args["events"])
        return _json_result(result)

    # -- Fleet ----------------------------------------------------------------

    @tool(
        "sigmashake_fleet_status",
        "Get fleet-wide status summary (total, online, degraded, offline agents)",
        {},
    )
    async def fleet_status(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.fleet.status()
        return _json_result(result)

    @tool(
        "sigmashake_fleet_list_agents",
        "List agents in the fleet with optional status filter",
        {"status": str, "limit": int, "offset": int},
    )
    async def fleet_list_agents(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.fleet.list_agents(
            status=args.get("status"),
            limit=args.get("limit", 100),
            offset=args.get("offset", 0),
        )
        return _json_result(result)

    @tool(
        "sigmashake_fleet_get_agent",
        "Get detailed info for a specific fleet agent",
        {"agent_id": str},
    )
    async def fleet_get_agent(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.fleet.get_agent(agent_id=args["agent_id"])
        return _json_result(result)

    @tool(
        "sigmashake_fleet_send_command",
        "Send a command to a specific fleet agent (restart, pause, resume, etc.)",
        {"agent_id": str, "command_type": str, "payload": dict},
    )
    async def fleet_send_command(args: Dict[str, Any]) -> Dict[str, Any]:
        from .models import FleetCommand
        cmd = FleetCommand(
            command_type=args["command_type"],
            payload=args.get("payload", {}),
        )
        result = client.fleet.send_command(agent_id=args["agent_id"], command=cmd)
        return _json_result(result)

    @tool(
        "sigmashake_fleet_broadcast",
        "Broadcast a command to all fleet agents",
        {"command_type": str, "payload": dict},
    )
    async def fleet_broadcast(args: Dict[str, Any]) -> Dict[str, Any]:
        from .models import FleetCommand
        cmd = FleetCommand(
            command_type=args["command_type"],
            payload=args.get("payload", {}),
        )
        result = client.fleet.broadcast(command=cmd)
        return _json_result(result)

    @tool(
        "sigmashake_fleet_agent_metrics",
        "Get resource metrics for a specific fleet agent",
        {"agent_id": str, "period": str},
    )
    async def fleet_agent_metrics(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.fleet.get_metrics(
            agent_id=args["agent_id"],
            period=args.get("period"),
        )
        return _json_result(result)

    @tool(
        "sigmashake_fleet_command_history",
        "Get command history for a specific fleet agent",
        {"agent_id": str, "limit": int, "offset": int},
    )
    async def fleet_command_history(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.fleet.get_command_history(
            agent_id=args["agent_id"],
            limit=args.get("limit", 100),
            offset=args.get("offset", 0),
        )
        return _json_result(result)

    # -- Gateway --------------------------------------------------------------

    @tool(
        "sigmashake_gateway_intercept_pre",
        "Run a pre-execution gateway intercept on a tool call",
        {"name": str, "input": dict, "session_id": str, "agent_id": str},
    )
    async def gateway_intercept_pre(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.gateway.intercept_pre(
            name=args["name"],
            input=args["input"],
            session_id=args["session_id"],
            agent_id=args["agent_id"],
        )
        return _json_result(result)

    @tool(
        "sigmashake_gateway_intercept_post",
        "Run a post-execution gateway intercept on a tool call result",
        {"name": str, "input": dict, "output": dict, "session_id": str, "agent_id": str},
    )
    async def gateway_intercept_post(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.gateway.intercept_post(
            name=args["name"],
            input=args["input"],
            output=args.get("output"),
            session_id=args["session_id"],
            agent_id=args["agent_id"],
        )
        return _json_result(result)

    # -- Accounts -------------------------------------------------------------

    @tool(
        "sigmashake_get_account",
        "Get account details by ID",
        {"account_id": str},
    )
    async def get_account(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.accounts.get(account_id=args["account_id"])
        return _json_result(result)

    @tool(
        "sigmashake_get_account_usage",
        "Get usage metrics for an account",
        {"account_id": str},
    )
    async def get_account_usage(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.accounts.get_usage(account_id=args["account_id"])
        return _json_result(result)

    @tool(
        "sigmashake_get_subscription",
        "Get subscription details for an account",
        {"account_id": str},
    )
    async def get_subscription(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.accounts.get_subscription(account_id=args["account_id"])
        return _json_result(result)

    # -- Auth -----------------------------------------------------------------

    @tool(
        "sigmashake_create_token",
        "Create an auth token for an agent with specified scopes",
        {"agent_id": str, "scopes": list},
    )
    async def create_token(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.auth.create_token(
            agent_id=args["agent_id"],
            scopes=args.get("scopes"),
        )
        return _json_result(result)

    # -- Triggers -------------------------------------------------------------

    @tool(
        "sigmashake_create_trigger",
        "Create a remote trigger for an agent",
        {
            "agent_id": str,
            "name": str,
            "prompt": str,
            "tools": list,
            "max_turns": int,
            "model": str,
            "schedule": str,
        },
    )
    async def create_trigger(args: Dict[str, Any]) -> Dict[str, Any]:
        body: Dict[str, Any] = {
            "name": args["name"],
            "prompt": args["prompt"],
        }
        if args.get("tools") is not None:
            body["tools"] = args["tools"]
        if args.get("max_turns") is not None:
            body["max_turns"] = args["max_turns"]
        else:
            body["max_turns"] = 10
        if args.get("model") is not None:
            body["model"] = args["model"]
        if args.get("schedule") is not None:
            body["schedule"] = args["schedule"]
        result = client.agents.create_trigger(args["agent_id"], body)
        return _json_result(result)

    @tool(
        "sigmashake_list_triggers",
        "List remote triggers for an agent",
        {"agent_id": str},
    )
    async def list_triggers(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.agents.list_triggers(args["agent_id"])
        return _json_result(result)

    @tool(
        "sigmashake_execute_trigger",
        "Execute a remote trigger for an agent",
        {"agent_id": str, "trigger_id": str},
    )
    async def execute_trigger(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.agents.execute_trigger(args["agent_id"], args["trigger_id"])
        return _json_result(result)

    @tool(
        "sigmashake_get_trigger_status",
        "Get execution status of a remote trigger",
        {"agent_id": str, "trigger_id": str},
    )
    async def get_trigger_status(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.agents.get_trigger_status(args["agent_id"], args["trigger_id"])
        return _json_result(result)

    @tool(
        "sigmashake_delete_trigger",
        "Delete a remote trigger for an agent",
        {"agent_id": str, "trigger_id": str},
    )
    async def delete_trigger(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.agents.delete_trigger(args["agent_id"], args["trigger_id"])
        return _json_result(result)

    # -- Context --------------------------------------------------------------

    @tool(
        "sigmashake_store_context",
        "Store conversation context for an agent",
        {"agent_id": str, "conversation_context": dict, "system_prompt": str, "tool_config": dict},
    )
    async def store_context(args: Dict[str, Any]) -> Dict[str, Any]:
        body: Dict[str, Any] = {
            "conversation_context": args["conversation_context"],
        }
        if args.get("system_prompt") is not None:
            body["system_prompt"] = args["system_prompt"]
        if args.get("tool_config") is not None:
            body["tool_config"] = args["tool_config"]
        result = client.agents.store_context(args["agent_id"], body)
        return _json_result(result)

    @tool(
        "sigmashake_get_context",
        "Get stored conversation context for an agent",
        {"agent_id": str},
    )
    async def get_context(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.agents.get_context(args["agent_id"])
        return _json_result(result)

    @tool(
        "sigmashake_delete_context",
        "Delete stored conversation context for an agent",
        {"agent_id": str},
    )
    async def delete_context(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.agents.delete_context(args["agent_id"])
        return _json_result(result)

    # -- Agent Tools ----------------------------------------------------------

    @tool(
        "sigmashake_register_tools",
        "Register tools for an agent",
        {"agent_id": str, "tools": list},
    )
    async def register_tools(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.agents.register_tools(args["agent_id"], args["tools"])
        return _json_result(result)

    @tool(
        "sigmashake_list_agent_tools",
        "List registered tools for an agent",
        {"agent_id": str},
    )
    async def list_agent_tools(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.agents.list_tools(args["agent_id"])
        return _json_result(result)

    @tool(
        "sigmashake_unregister_tool",
        "Unregister a tool from an agent",
        {"agent_id": str, "tool_name": str},
    )
    async def unregister_tool(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.agents.unregister_tool(args["agent_id"], args["tool_name"])
        return _json_result(result)

    # -- Agent Usage ----------------------------------------------------------

    @tool(
        "sigmashake_get_agent_usage",
        "Get usage metrics for an agent",
        {"agent_id": str, "from_date": str, "to_date": str},
    )
    async def get_agent_usage(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.agents.get_usage(
            args["agent_id"],
            from_date=args.get("from_date"),
            to_date=args.get("to_date"),
        )
        return _json_result(result)

    # -- DB (remaining) -------------------------------------------------------

    @tool(
        "sigmashake_db_scroll",
        "Scroll through large database result sets with cursor-based pagination",
        {"table_name": str, "batch_size": int, "cursor": str, "filters": list},
    )
    async def db_scroll(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.db.scroll(
            table_name=args["table_name"],
            batch_size=args.get("batch_size", 100),
            cursor=args.get("cursor"),
            filters=args.get("filters"),
        )
        return _json_result(result)

    @tool(
        "sigmashake_db_insert",
        "Insert rows into a SigmaShake database table",
        {"table_name": str, "columns": list},
    )
    async def db_insert(args: Dict[str, Any]) -> Dict[str, Any]:
        result = client.db.insert(
            table_name=args["table_name"],
            columns=args["columns"],
        )
        return _json_result(result)

    return [
        # Documents
        search_documents,
        # DB
        query_db,
        vector_search,
        db_scroll,
        db_insert,
        # Memory
        store_memory,
        recall_memory,
        get_memory,
        delete_memory,
        # SOC
        list_alerts,
        get_timeline,
        # Shield
        shield_scan,
        shield_register,
        # Pulse
        pipeline_status,
        pipeline_metrics,
        bottlenecks,
        ai_brief,
        get_pipeline_runs,
        get_pipeline_run,
        trigger_pipeline,
        push_events,
        # Agents
        list_agents,
        register_agent,
        get_agent,
        update_agent,
        # Fleet
        fleet_status,
        fleet_list_agents,
        fleet_get_agent,
        fleet_send_command,
        fleet_broadcast,
        fleet_agent_metrics,
        fleet_command_history,
        # Gateway
        gateway_intercept_pre,
        gateway_intercept_post,
        # Accounts
        get_account,
        get_account_usage,
        get_subscription,
        # Auth
        create_token,
        # Triggers
        create_trigger,
        list_triggers,
        execute_trigger,
        get_trigger_status,
        delete_trigger,
        # Context
        store_context,
        get_context,
        delete_context,
        # Agent Tools
        register_tools,
        list_agent_tools,
        unregister_tool,
        # Agent Usage
        get_agent_usage,
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
