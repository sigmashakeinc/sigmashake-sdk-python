# sigmashake

Python SDK for the SigmaShake platform API.

## Installation

```bash
pip install sigmashake
```

## Quick Start

```python
import sigmashake

client = sigmashake.SigmaShake(api_key="sk-...")
my_tool = client.gateway.wrap(my_agent_function)
# All calls to my_tool are now intercepted, logged, and policy-checked
```

### Test connectivity

```python
print(client.ping())  # {"status": "ok", "latency_ms": 23}
```

### Add multiple tools at once

```python
search = client.gateway.wrap(search_fn)
write_file = client.gateway.wrap(write_file_fn)
query_db = client.gateway.wrap(query_db_fn)
```

### More examples

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

## API Reference

### `SigmaShake` — Main Client

```python
client = SigmaShake(api_key="sk-...", base_url="https://api.sigmashake.com", timeout=30.0)
```

| Attribute | Type | Description |
|-----------|------|-------------|
| `auth` | `AuthResource` | Token creation and validation |
| `shield` | `ShieldResource` | Agent registration and operation scanning |
| `memory` | `MemoryResource` | Key-value memory store per agent |
| `agents` | `AgentsResource` | Agent CRUD and listing |
| `accounts` | `AccountsResource` | Account management |
| `fleet` | `FleetResource` | Fleet registration and status |
| `gateway` | `GatewayResource` | Gateway log retrieval |
| `soc` | `SocResource` | Incidents and SOC operations |
| `pulse` | `PulseResource` | Platform health and bottleneck reporting |
| `db` | `DbResource` | Database query interface |

### `AuthResource`

| Method | Description |
|--------|-------------|
| `create_token(agent_id, scopes, ttl_secs)` | Create a scoped auth token |
| `validate_token(token)` | Validate a token and return claims |

### `ShieldResource`

| Method | Description |
|--------|-------------|
| `register_agent(agent_id, agent_type, session_ttl_secs)` | Register an agent session |
| `scan(agent_id, session_id, operation)` | Scan an operation for policy violations |
| `end_session(session_id)` | End an active agent session |

### `MemoryResource`

| Method | Description |
|--------|-------------|
| `store(key, value, tags)` | Store a key-value pair |
| `retrieve(key)` | Retrieve a stored value |
| `list(tags)` | List memory entries matching tags |
| `delete(key)` | Delete a memory entry |

### Exceptions

| Exception | Description |
|-----------|-------------|
| `SigmaShakeError` | Base exception for all SDK errors |
| `AuthenticationError` | Invalid or missing API key |
| `AuthorizationError` | Insufficient permissions |
| `NotFoundError` | Requested resource not found |
| `ValidationError` | Request validation failure |
| `RateLimitError` | Rate limit exceeded |
| `ServerError` | Server-side error |

## Documentation

Build Sphinx HTML docs locally:

```bash
pip install sigmashake[dev]
make docs
# Output in docs/_build/html/index.html
```

## License

MIT
