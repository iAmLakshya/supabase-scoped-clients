"""
Supabase Scoped Clients - Examples

Demonstrates user impersonation with RLS enforcement.
Run: poetry run python examples/example.py

Prerequisites:
- Local Supabase running (supabase start)
- Environment variables set (see examples/README.md)
"""

import asyncio
import uuid

from supabase_scoped_clients import (
    ScopedClientBuilder,
    get_async_client,
    get_client,
)


def basic_usage():
    """Basic CRUD operations with a scoped client."""
    user_id = str(uuid.uuid4())
    client = get_client(user_id)

    note = (
        client.table("notes")
        .insert({"user_id": user_id, "title": "My Note", "content": "Hello world"})
        .execute()
        .data[0]
    )

    notes = client.table("notes").select("*").execute().data
    assert len(notes) == 1

    updated = (
        client.table("notes")
        .update({"title": "Updated Note"})
        .eq("id", note["id"])
        .execute()
        .data[0]
    )
    assert updated["title"] == "Updated Note"

    client.table("notes").delete().eq("id", note["id"]).execute()


def rls_isolation():
    """Verify that RLS properly isolates data between users."""
    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())
    client_a = get_client(user_a)
    client_b = get_client(user_b)

    # User A creates a note
    note_a = (
        client_a.table("notes")
        .insert({"user_id": user_a, "title": "User A's Secret", "content": "Private"})
        .execute()
        .data[0]
    )

    # User B cannot see User A's note
    user_b_sees = client_b.table("notes").select("*").execute().data
    assert len(user_b_sees) == 0, "RLS violation: User B can see User A's data!"

    # User B creates their own note
    note_b = (
        client_b.table("notes")
        .insert({"user_id": user_b, "title": "User B's Note", "content": "Also private"})
        .execute()
        .data[0]
    )

    # Each user sees only their own data
    assert len(client_a.table("notes").select("*").execute().data) == 1
    assert len(client_b.table("notes").select("*").execute().data) == 1

    # User B cannot update User A's note
    result = (
        client_b.table("notes")
        .update({"title": "Hacked!"})
        .eq("id", note_a["id"])
        .execute()
    )
    assert len(result.data) == 0, "RLS violation: User B modified User A's data!"

    # Cleanup
    client_a.table("notes").delete().eq("id", note_a["id"]).execute()
    client_b.table("notes").delete().eq("id", note_b["id"]).execute()


async def async_usage():
    """Async client usage with get_async_client()."""
    user_id = str(uuid.uuid4())
    client = await get_async_client(user_id)

    note = (
        await client.table("notes")
        .insert({"user_id": user_id, "title": "Async Note", "content": "Created async"})
        .execute()
    ).data[0]

    notes = (await client.table("notes").select("*").execute()).data
    assert len(notes) == 1

    await client.table("notes").delete().eq("id", note["id"]).execute()


def builder_pattern():
    """ScopedClientBuilder for custom claims and expiry."""
    user_id = str(uuid.uuid4())

    client = (
        ScopedClientBuilder(user_id)
        .with_claims({"org_id": "org-123", "role": "admin"})
        .with_expiry(7200)  # 2 hours
        .build()
    )

    note = (
        client.table("notes")
        .insert({"user_id": user_id, "title": "Multi-tenant Note", "content": "With org_id"})
        .execute()
        .data[0]
    )

    client.table("notes").delete().eq("id", note["id"]).execute()


if __name__ == "__main__":
    basic_usage()
    rls_isolation()
    asyncio.run(async_usage())
    builder_pattern()
    print("All examples passed!")
