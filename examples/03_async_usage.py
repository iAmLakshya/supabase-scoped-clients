"""
Async Usage Example

Demonstrates async client usage with get_async_client().
Shows the same CRUD operations as the basic example, but in an async context.

Run with: poetry run python examples/03_async_usage.py
"""

import asyncio
import uuid

from supabase_scoped_clients import get_async_client


async def main():
    # Create a unique user ID for this example
    user_id = str(uuid.uuid4())
    print(f"Creating async scoped client for user: {user_id}")

    # Get an async scoped client
    # Note: get_async_client() is async because the underlying Supabase
    # async client creation (acreate_client) is async
    client = await get_async_client(user_id)

    # Insert a note (async)
    print("\n1. Inserting a note (async)...")
    insert_response = await (
        client.table("notes")
        .insert(
            {
                "user_id": user_id,
                "title": "Async Note",
                "content": "This note was created using the async client.",
            }
        )
        .execute()
    )
    note = insert_response.data[0]
    note_id = note["id"]
    print(f"   Created note with ID: {note_id}")

    # Read notes back (async)
    print("\n2. Reading all notes (async)...")
    select_response = await client.table("notes").select("*").execute()
    print(f"   Found {len(select_response.data)} note(s)")
    for row in select_response.data:
        print(f"   - {row['title']}")

    # Update the note (async)
    print("\n3. Updating the note (async)...")
    update_response = await (
        client.table("notes")
        .update({"title": "Updated Async Note"})
        .eq("id", note_id)
        .execute()
    )
    print(f"   New title: {update_response.data[0]['title']}")

    # Delete the note (async)
    print("\n4. Deleting the note (async)...")
    delete_response = await client.table("notes").delete().eq("id", note_id).execute()
    print(f"   Deleted {len(delete_response.data)} note(s)")

    print("\nAsync usage example complete!")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
