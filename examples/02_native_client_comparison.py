"""
Native Client Comparison

Shows that switching from native Supabase client to scoped client
requires ONLY changing initialization - all other code stays the same.

Run: poetry run python examples/02_native_client_comparison.py
"""

import uuid

# ============================================================
# BEFORE: Native Supabase client (no user impersonation)
# ============================================================
# from supabase import create_client
# client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================================================
# AFTER: Scoped client (user impersonation with RLS)
# ============================================================
from supabase_scoped_clients import get_client

user_id = str(uuid.uuid4())
client = get_client(user_id)

# ============================================================
# ALL CODE BELOW IS IDENTICAL TO NATIVE CLIENT USAGE
# ============================================================

# Insert
response = client.table("notes").insert({
    "user_id": user_id,
    "title": "Test Note",
    "content": "Same API as native client"
}).execute()
note_id = response.data[0]["id"]

# Select
response = client.table("notes").select("*").execute()

# Select with filter
response = client.table("notes").select("title, content").eq("id", note_id).execute()

# Update
response = client.table("notes").update({"title": "Updated"}).eq("id", note_id).execute()

# Delete
response = client.table("notes").delete().eq("id", note_id).execute()
