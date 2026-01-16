"""
Builder Pattern Example

Demonstrates the ScopedClientBuilder for advanced configuration:
- Custom claims (e.g., org_id for multi-tenant applications)
- Custom token expiry
- When to prefer the builder over factory functions

Run with: poetry run python examples/04_builder_pattern.py
"""

import uuid

from supabase_scoped_clients import ScopedClientBuilder


def main():
    user_id = str(uuid.uuid4())
    org_id = "org-123"

    print("Builder Pattern Example")
    print("=" * 60)
    print(f"User ID: {user_id}")
    print(f"Org ID: {org_id}")

    # Build a client with custom configuration using fluent API
    print("\n1. Building client with custom claims and expiry...")
    print("""
    client = (
        ScopedClientBuilder(user_id)
        .with_claims({"org_id": org_id, "role": "admin"})
        .with_expiry(7200)  # 2 hours
        .build()
    )
    """)

    client = (
        ScopedClientBuilder(user_id)
        .with_claims({"org_id": org_id, "role": "admin"})
        .with_expiry(7200)  # 2 hours
        .build()
    )

    # Use it like any Supabase client
    print("2. Using the client (same API as always)...")
    response = (
        client.table("notes")
        .insert(
            {
                "user_id": user_id,
                "title": "Multi-tenant Note",
                "content": f"This note belongs to organization {org_id}",
            }
        )
        .execute()
    )
    note_id = response.data[0]["id"]
    print(f"   Created note: {note_id}")

    # Clean up
    client.table("notes").delete().eq("id", note_id).execute()
    print("   Cleaned up test data")

    # When to use builder vs factory
    print("\n" + "=" * 60)
    print("WHEN TO USE WHAT")
    print("=" * 60)
    print("""
Factory Functions (get_client, get_async_client):
  - Simple cases where you just need user impersonation
  - Default token expiry (1 hour) is acceptable
  - No custom claims needed

  Example:
    client = get_client(user_id)

Builder Pattern (ScopedClientBuilder, AsyncScopedClientBuilder):
  - Multi-tenant apps needing org_id or tenant claims
  - Custom roles beyond the standard "authenticated"
  - Custom token expiry (shorter for security, longer for convenience)
  - Any scenario requiring non-default JWT claims

  Example:
    client = (
        ScopedClientBuilder(user_id)
        .with_claims({"org_id": "...", "permissions": [...]})
        .with_expiry(900)  # 15 minutes
        .build()
    )
""")


if __name__ == "__main__":
    main()
