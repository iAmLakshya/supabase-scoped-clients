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
    print("1. Basic Usage")
    user_id = str(uuid.uuid4())
    client = get_client(user_id)

    note = (
        client.table("notes")
        .insert({"user_id": user_id, "title": "My Note", "content": "Hello world"})
        .execute()
        .data[0]
    )
    print(f"   Created note: {note['id']}")

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
    print("   Updated note")

    client.table("notes").delete().eq("id", note["id"]).execute()
    print("   Deleted note")


def rls_isolation():
    """Verify that RLS properly isolates data between users."""
    print("2. RLS Isolation")
    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())
    client_a = get_client(user_a)
    client_b = get_client(user_b)

    note_a = (
        client_a.table("notes")
        .insert({"user_id": user_a, "title": "User A's Secret", "content": "Private"})
        .execute()
        .data[0]
    )
    print(f"   User A created note: {note_a['id']}")

    user_b_sees = client_b.table("notes").select("*").execute().data
    assert len(user_b_sees) == 0, "RLS violation: User B can see User A's data!"
    print("   User B cannot see User A's note ✓")

    note_b = (
        client_b.table("notes")
        .insert(
            {"user_id": user_b, "title": "User B's Note", "content": "Also private"}
        )
        .execute()
        .data[0]
    )

    assert len(client_a.table("notes").select("*").execute().data) == 1
    assert len(client_b.table("notes").select("*").execute().data) == 1
    print("   Each user sees only their own data ✓")

    result = (
        client_b.table("notes")
        .update({"title": "Hacked!"})
        .eq("id", note_a["id"])
        .execute()
    )
    assert len(result.data) == 0, "RLS violation: User B modified User A's data!"
    print("   User B cannot modify User A's note ✓")

    client_a.table("notes").delete().eq("id", note_a["id"]).execute()
    client_b.table("notes").delete().eq("id", note_b["id"]).execute()


async def async_usage():
    """Async client usage with get_async_client()."""
    print("3. Async Usage")
    user_id = str(uuid.uuid4())
    client = await get_async_client(user_id)

    note = (
        await client.table("notes")
        .insert({"user_id": user_id, "title": "Async Note", "content": "Created async"})
        .execute()
    ).data[0]
    print(f"   Created async note: {note['id']}")

    notes = (await client.table("notes").select("*").execute()).data
    assert len(notes) == 1

    await client.table("notes").delete().eq("id", note["id"]).execute()
    print("   Deleted async note")


def builder_pattern():
    """ScopedClientBuilder for custom claims and expiry."""
    print("4. Builder Pattern")
    user_id = str(uuid.uuid4())

    client = (
        ScopedClientBuilder(user_id)
        .with_claims({"org_id": "org-123", "role": "admin"})
        .with_expiry(7200)
        .build()
    )
    print("   Built client with custom claims: org_id=org-123, role=admin")

    note = (
        client.table("notes")
        .insert(
            {"user_id": user_id, "title": "Multi-tenant Note", "content": "With org_id"}
        )
        .execute()
        .data[0]
    )
    print(f"   Created note: {note['id']}")

    client.table("notes").delete().eq("id", note["id"]).execute()
    print("   Deleted note")


if __name__ == "__main__":
    basic_usage()
    rls_isolation()
    asyncio.run(async_usage())
    builder_pattern()
    print("\nAll examples passed!")
