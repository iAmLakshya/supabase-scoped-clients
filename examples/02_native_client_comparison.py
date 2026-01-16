"""
Native Client Comparison Example

This example demonstrates that switching from native Supabase client
to scoped client requires ONLY changing the client initialization.
All other code remains exactly the same.

Run with: poetry run python examples/02_native_client_comparison.py
"""

import uuid

# ============================================================
# BEFORE: Native Supabase client (no user impersonation)
# ============================================================
# from supabase import create_client
# import os
#
# SUPABASE_URL = os.environ["SUPABASE_URL"]
# SUPABASE_KEY = os.environ["SUPABASE_KEY"]
#
# client = create_client(SUPABASE_URL, SUPABASE_KEY)
#
# With native client:
# - All requests use the anon/service role
# - RLS policies see NULL for auth.uid()
# - No user-specific data isolation

# ============================================================
# AFTER: Scoped client (user impersonation with RLS)
# ============================================================
from supabase_scoped_clients import get_client

user_id = str(uuid.uuid4())
client = get_client(user_id)

# With scoped client:
# - Requests include a JWT with the user's ID
# - RLS policies see the user's ID via auth.uid()
# - Data is automatically isolated to this user

# ============================================================
# THE REST OF YOUR CODE STAYS EXACTLY THE SAME
# ============================================================
# The scoped client exposes the exact same API as the native client.
# You can use .table(), .from_(), .rpc(), .storage, .auth, etc.


def main():
    print(f"User ID: {user_id}")
    print("\nDemonstrating API compatibility with native Supabase client...")

    # INSERT - exactly the same as native client
    print("\n1. Insert (same API as native client)")
    print('   client.table("notes").insert({...}).execute()')
    response = (
        client.table("notes")
        .insert(
            {
                "user_id": user_id,
                "title": "Comparison Note",
                "content": "This uses the exact same API as the native Supabase client.",
            }
        )
        .execute()
    )
    note_id = response.data[0]["id"]
    print(f"   Result: Created note {note_id}")

    # SELECT - exactly the same as native client
    print("\n2. Select (same API as native client)")
    print('   client.table("notes").select("*").execute()')
    response = client.table("notes").select("*").execute()
    print(f"   Result: Found {len(response.data)} note(s)")

    # SELECT with filter - exactly the same as native client
    print("\n3. Select with filter (same API as native client)")
    print('   client.table("notes").select("title, content").eq("id", note_id).execute()')
    response = client.table("notes").select("title, content").eq("id", note_id).execute()
    print(f"   Result: {response.data[0]}")

    # UPDATE - exactly the same as native client
    print("\n4. Update (same API as native client)")
    print('   client.table("notes").update({...}).eq("id", note_id).execute()')
    response = (
        client.table("notes")
        .update({"title": "Updated Comparison Note"})
        .eq("id", note_id)
        .execute()
    )
    print(f"   Result: Updated title to '{response.data[0]['title']}'")

    # DELETE - exactly the same as native client
    print("\n5. Delete (same API as native client)")
    print('   client.table("notes").delete().eq("id", note_id).execute()')
    response = client.table("notes").delete().eq("id", note_id).execute()
    print(f"   Result: Deleted {len(response.data)} note(s)")

    print("\n" + "=" * 60)
    print("KEY TAKEAWAY")
    print("=" * 60)
    print("""
Only the initialization changed:

  BEFORE (native):
    from supabase import create_client
    client = create_client(url, key)

  AFTER (scoped):
    from supabase_scoped_clients import get_client
    client = get_client(user_id)

All other code (.table(), .insert(), .select(), etc.) stays the same!
This is 100% API compatible with the native Supabase Python client.
""")


if __name__ == "__main__":
    main()
