# sigmashake

Python SDK for the SigmaShake platform API.

## Installation

```bash
pip install sigmashake
```

## Quick Start

```python
from sigmashake import SigmaShake

client = SigmaShake(api_key="sk-...")

# Create an auth token
token = client.auth.create_token(agent_id="agent-1", scopes=["read", "write"])

# Register an agent with Shield
session = client.shield.register_agent(
    agent_id="agent-1",
    agent_type="coding",
    session_ttl_secs=3600,
)

# Store agent memory
client.memory.store(key="context", value="important data", tags=["session-1"])

# Query the database
results = client.db.query("events", filters=[{"column": "id", "op": "gt", "value": 1}])
```

## Async Usage

```python
from sigmashake import SigmaShake

async with SigmaShake(api_key="sk-...", async_mode=True) as client:
    token = await client.auth.create_token(agent_id="agent-1", scopes=["read"])
```

## License

MIT
