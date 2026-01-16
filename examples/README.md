# Examples

Runnable examples demonstrating `supabase-scoped-clients` usage.

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

Set these environment variables for the examples:

```bash
export SUPABASE_URL="http://127.0.0.1:54331"
export SUPABASE_KEY="sb_publishable_ACJWlzQHlZjBrEguHvfOxg_3BJgxAaH"
export SUPABASE_JWT_SECRET="super-secret-jwt-token-with-at-least-32-characters-long"
```

Or create a `.env` file in the project root with these values.

## Running Examples

From the project root:

```bash
# Basic CRUD operations
poetry run python examples/01_basic_usage.py

# Native client comparison (shows API compatibility)
poetry run python examples/02_native_client_comparison.py

# Async client usage
poetry run python examples/03_async_usage.py

# Builder pattern for advanced configuration
poetry run python examples/04_builder_pattern.py
```

## Example Descriptions

### 01_basic_usage.py
Demonstrates basic synchronous client usage: creating a scoped client for a user and performing CRUD operations on the `notes` table. Shows that RLS policies automatically filter data to the authenticated user.

### 02_native_client_comparison.py
Side-by-side comparison showing that switching from native Supabase client to scoped client requires **only changing the initialization**. All other code (queries, inserts, updates, deletes) remains exactly the same.

### 03_async_usage.py
Demonstrates async client usage with `get_async_client()`. Shows the same CRUD operations in an async context using `asyncio`.

### 04_builder_pattern.py
Demonstrates the `ScopedClientBuilder` for advanced configuration: custom claims (e.g., `org_id` for multi-tenant apps), custom token expiry, and when to prefer the builder over factory functions.

## Key Takeaway

The scoped client API is **100% compatible** with the native Supabase Python client. You can migrate existing code by changing only the client initialization - no other code changes required.
