# Examples

Runnable example demonstrating `supabase-scoped-clients` usage.

## Prerequisites

1. **Local Supabase running**
   ```bash
   supabase start
   ```

2. **Migrations applied** (includes the `notes` table with RLS)
   ```bash
   supabase db reset
   ```

3. **Package installed** (from project root)
   ```bash
   poetry install
   ```

## Environment Setup

Set these environment variables:

```bash
export SUPABASE_URL="http://127.0.0.1:54331"
export SUPABASE_KEY="<your-anon-key>"
export SUPABASE_JWT_SECRET="super-secret-jwt-token-with-at-least-32-characters-long"
```

Or create a `.env` file in the project root.

## Running

```bash
poetry run python examples/example.py
```

## What It Demonstrates

1. **Basic Usage** - Creating a scoped client and performing CRUD operations
2. **RLS Isolation** - Verifying that User B cannot see or modify User A's data
3. **Native Client Compatibility** - Only initialization changes, all other code stays the same
4. **Async Usage** - Using `get_async_client()` with asyncio
5. **Builder Pattern** - Custom claims and expiry with `ScopedClientBuilder`

## Key Takeaway

The scoped client API is **100% compatible** with the native Supabase Python client. Migrate existing code by changing only the client initialization.
