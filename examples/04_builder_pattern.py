"""
Builder Pattern Example

Use ScopedClientBuilder for advanced configuration:
- Custom claims (org_id, tenant, permissions)
- Custom token expiry

Run: poetry run python examples/04_builder_pattern.py
"""

import uuid

from supabase_scoped_clients import ScopedClientBuilder

user_id = str(uuid.uuid4())

# Builder with custom claims and expiry
client = (
    ScopedClientBuilder(user_id)
    .with_claims({"org_id": "org-123", "role": "admin"})
    .with_expiry(7200)  # 2 hours
    .build()
)

# Use like any Supabase client
note = (
    client.table("notes")
    .insert({"user_id": user_id, "title": "Multi-tenant Note", "content": "With org_id claim"})
    .execute()
    .data[0]
)

client.table("notes").delete().eq("id", note["id"]).execute()


# ============================================================
# WHEN TO USE WHAT
# ============================================================
#
# Factory (get_client, get_async_client):
#   - Simple user impersonation
#   - Default 1-hour expiry is fine
#   - No custom claims needed
#
# Builder (ScopedClientBuilder, AsyncScopedClientBuilder):
#   - Multi-tenant apps (org_id, tenant claims)
#   - Custom roles or permissions
#   - Non-default token expiry
