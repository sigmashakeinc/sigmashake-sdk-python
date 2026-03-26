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

## OpenAPI Drift Detection

Models in `src/sigmashake/models.py` must match the canonical OpenAPI spec in
`sigmashake-openapi/openapi.yaml`. A drift detector validates that all schemas
and fields in the spec are represented in the SDK.

```bash
# From SDK root (requires sigmashake-openapi as sibling)
python3 scripts/validate_models.py

# JSON output for CI
python3 scripts/validate_models.py --json

# Or from the openapi repo
cd ../sigmashake-openapi
./validate-sdks.sh --python
```

The validator exits non-zero when drift is detected. Run it before submitting
changes to `models.py` and after any OpenAPI spec updates.

## License

MIT
