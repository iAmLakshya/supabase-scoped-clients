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

# ============================================================
# 1. BASIC USAGE
# ============================================================

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


# ============================================================
# 2. RLS ISOLATION VERIFICATION
# ============================================================

# User A creates a note
user_a = str(uuid.uuid4())
client_a = get_client(user_a)
note_a = (
    client_a.table("notes")
    .insert({"user_id": user_a, "title": "User A's Secret", "content": "Private data"})
    .execute()
    .data[0]
)

# User B cannot see User A's note
user_b = str(uuid.uuid4())
client_b = get_client(user_b)
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

# User B cannot update User A's note (RLS blocks it)
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


# ============================================================
# 3. NATIVE CLIENT COMPARISON
# ============================================================
# Only the initialization changes - all other code stays the same.
#
# BEFORE (native):
#   from supabase import create_client
#   client = create_client(SUPABASE_URL, SUPABASE_KEY)
#
# AFTER (scoped):
#   from supabase_scoped_clients import get_client
#   client = get_client(user_id)
#
# All .table(), .select(), .insert(), .update(), .delete() calls are identical.


# ============================================================
# 4. ASYNC USAGE
# ============================================================

async def async_example():
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


asyncio.run(async_example())


# ============================================================
# 5. BUILDER PATTERN (Advanced Configuration)
# ============================================================
# Use when you need custom claims or non-default expiry.

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


# ============================================================
# CLEANUP
# ============================================================

# Clean up the note from section 1
client = get_client(user_id)
client.table("notes").delete().neq("id", "").execute()

print("All examples passed successfully!")
