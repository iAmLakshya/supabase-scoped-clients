# supabase-scoped-clients

Stateless user impersonation for Supabase with Row Level Security (RLS).

## What This Solves

Server-side Supabase applications often need to execute database operations on behalf of users while respecting RLS policies. The traditional approach uses OTP-based session generation, but this has a critical flaw: only one active OTP exists per user, causing race conditions when multiple services impersonate the same user simultaneously.

**This library solves the problem** by generating self-signed JWT tokens that Supabase accepts for RLS evaluation. Each token is independently generated with no shared state, enabling unlimited concurrent sessions per user across any number of services.

## Quick Start

Set environment variables:

```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_KEY="your-anon-or-service-key"
export SUPABASE_JWT_SECRET="your-jwt-secret"
```

Create a user-scoped client:

```python
from supabase_scoped_clients import get_client

client = get_client("user-uuid-here")
data = client.table("notes").select("*").execute()
```

The client now operates as that user, and RLS policies are enforced. Tokens are automatically refreshed before expiry.

## Configuration

### Environment Variables

The library reads configuration from these environment variables:

| Variable              | Description                                                      |
| --------------------- | ---------------------------------------------------------------- |
| `SUPABASE_URL`        | Your Supabase project URL                                        |
| `SUPABASE_KEY`        | Supabase anon key or service role key                            |
| `SUPABASE_JWT_SECRET` | JWT secret from Supabase dashboard (Settings > API > JWT Secret) |

### Programmatic Configuration

Override environment variables with explicit configuration:

```python
from supabase_scoped_clients import Config, get_client

config = Config(
    supabase_url="https://your-project.supabase.co",
    supabase_key="your-key",
    supabase_jwt_secret="your-jwt-secret",
)

client = get_client("user-uuid", config=config)
```

### Using load_config()

The `load_config()` helper provides better error messages:

```python
from supabase_scoped_clients import load_config, ConfigurationError

try:
    config = load_config()
except ConfigurationError as e:
    print(f"Configuration error in {e.field}: {e.reason}")
```

## Usage Examples

### Sync Client

```python
from supabase_scoped_clients import get_client

client = get_client("user-uuid")

# All operations execute as this user with auto-refresh enabled
data = client.table("notes").select("*").execute()
client.table("notes").insert({"title": "New Note"}).execute()
```

### Async Client

For async applications:

```python
from supabase_scoped_clients import get_async_client

client = await get_async_client("user-uuid")

data = await client.table("notes").select("*").execute()
await client.table("notes").insert({"title": "New Note"}).execute()
```

### All Parameters

Both `get_client` and `get_async_client` accept the same parameters:

```python
from supabase_scoped_clients import get_client

client = get_client(
    "user-uuid",
    config=config,                      # Optional: explicit config
    role="authenticated",               # JWT role (default: "authenticated")
    expiry_seconds=3600,                # Token validity (default: 1 hour)
    custom_claims={"tenant_id": "abc"}, # Additional JWT claims
    auto_refresh=True,                  # Auto-refresh tokens (default: True)
    refresh_threshold_seconds=60,       # Refresh 60s before expiry (default: 60)
)
```

### Disabling Auto-Refresh

For short-lived operations where auto-refresh isn't needed:

```python
from supabase_scoped_clients import get_client

# Get a bare client without auto-refresh
client = get_client("user-uuid", auto_refresh=False)
```

### Custom Claims for Multi-tenant RLS

Add custom claims to the JWT for use in RLS policies:

```python
from supabase_scoped_clients import get_client

client = get_client(
    "user-uuid",
    custom_claims={"tenant_id": "acme-corp", "subscription": "pro"}
)
```

These claims appear in `auth.jwt()` within your RLS policies:

```sql
-- RLS policy using custom claims
CREATE POLICY "tenant_isolation" ON documents
    FOR ALL
    USING (tenant_id = (auth.jwt() ->> 'tenant_id')::text);
```

## API Reference

### Factory Functions

**`get_client(user_id, *, config=None, role="authenticated", expiry_seconds=3600, custom_claims=None, auto_refresh=True, refresh_threshold_seconds=60)`**

Creates a sync Supabase client scoped to the specified user. Returns a native `supabase.Client`. By default, tokens auto-refresh before expiry.

**`get_async_client(user_id, *, config=None, role="authenticated", expiry_seconds=3600, custom_claims=None, auto_refresh=True, refresh_threshold_seconds=60)`**

Creates an async Supabase client scoped to the specified user. Returns a native `supabase.AsyncClient`. By default, tokens auto-refresh before expiry.

### Configuration

**`Config`**

Pydantic settings class. Fields: `supabase_url`, `supabase_key`, `supabase_jwt_secret`.

**`load_config(**kwargs)`**

Loads configuration from environment variables, converting validation errors to `ConfigurationError`.

### Exceptions

**`SupabaseScopedClientsError`** - Base exception for all library errors.

**`ConfigurationError`** - Raised when configuration is invalid or missing. Has `field` and `reason` attributes.

**`ClientError`** - Raised for client creation errors (e.g., empty user_id).

**`TokenError`** - Raised for JWT token generation errors.

## Token Auto-Refresh Behavior

By default, `get_client` and `get_async_client` return clients with automatic token management:

1. **Proactive refresh**: Tokens are refreshed before they expire, not after. The default threshold is 60 seconds before expiry.

2. **Single-flight pattern**: Concurrent operations share a single refresh. If multiple operations trigger refresh simultaneously, only one refresh occurs.

3. **Seamless operation**: No manual token management needed. The client intercepts method calls and ensures a valid token before execution.

Configure the refresh threshold based on your operation duration:

```python
# Refresh 2 minutes before expiry for long operations
client = get_client("user-uuid", refresh_threshold_seconds=120)
```

## Requirements

- Python >= 3.11
- pyjwt >= 2.8.0
- supabase >= 2.0.0
- pydantic-settings >= 2.0.0

## License

MIT
