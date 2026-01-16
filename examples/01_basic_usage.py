"""
Basic Usage Example

Demonstrates creating a scoped client and performing CRUD operations.

Run: poetry run python examples/01_basic_usage.py
"""

import uuid

from supabase_scoped_clients import get_client

user_id = str(uuid.uuid4())
client = get_client(user_id)

# Create
note = (
    client.table("notes")
    .insert({"user_id": user_id, "title": "My Note", "content": "Hello world"})
    .execute()
    .data[0]
)

# Read
notes = client.table("notes").select("*").execute().data

# Update
updated = (
    client.table("notes")
    .update({"title": "Updated Note"})
    .eq("id", note["id"])
    .execute()
    .data[0]
)

# Delete
client.table("notes").delete().eq("id", note["id"]).execute()

# Verify isolation - different user sees nothing
other_user = str(uuid.uuid4())
other_client = get_client(other_user)
assert other_client.table("notes").select("*").execute().data == []
