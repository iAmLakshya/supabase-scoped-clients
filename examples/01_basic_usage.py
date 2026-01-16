"""
Basic Usage Example

Demonstrates creating a scoped client for a user and performing
basic CRUD operations on the notes table.

Run with: poetry run python examples/01_basic_usage.py
"""

import uuid

from supabase_scoped_clients import get_client


def main():
    # Create a unique user ID for this example
    user_id = str(uuid.uuid4())
    print(f"Creating scoped client for user: {user_id}")

    # Get a scoped client - this creates a JWT token with the user's ID
    # and configures the client to send it with every request.
    # RLS policies will automatically filter data to this user.
    client = get_client(user_id)

    # Insert a note
    print("\n1. Inserting a note...")
    insert_response = (
        client.table("notes")
        .insert(
            {
                "user_id": user_id,
                "title": "My First Note",
                "content": "This is a test note created by the basic usage example.",
            }
        )
        .execute()
    )
    note = insert_response.data[0]
    note_id = note["id"]
    print(f"   Created note with ID: {note_id}")
    print(f"   Title: {note['title']}")

    # Read notes back
    print("\n2. Reading all notes for this user...")
    select_response = client.table("notes").select("*").execute()
    print(f"   Found {len(select_response.data)} note(s)")
    for row in select_response.data:
        print(f"   - {row['title']}: {row['content'][:50]}...")

    # Update the note
    print("\n3. Updating the note...")
    update_response = (
        client.table("notes")
        .update({"title": "My Updated Note", "content": "This content has been updated."})
        .eq("id", note_id)
        .execute()
    )
    updated_note = update_response.data[0]
    print(f"   New title: {updated_note['title']}")
    print(f"   New content: {updated_note['content']}")

    # Delete the note
    print("\n4. Deleting the note...")
    delete_response = client.table("notes").delete().eq("id", note_id).execute()
    print(f"   Deleted {len(delete_response.data)} note(s)")

    # Verify deletion
    print("\n5. Verifying deletion...")
    final_response = client.table("notes").select("*").eq("id", note_id).execute()
    print(f"   Notes remaining with that ID: {len(final_response.data)}")

    print("\nBasic usage example complete!")


if __name__ == "__main__":
    main()
