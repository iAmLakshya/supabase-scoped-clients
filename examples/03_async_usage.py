"""
Async Usage Example

Demonstrates async client usage with get_async_client().

Run: poetry run python examples/03_async_usage.py
"""

import asyncio
import uuid

from supabase_scoped_clients import get_async_client


async def main():
    user_id = str(uuid.uuid4())
    client = await get_async_client(user_id)

    # Create
    note = (
        await client.table("notes")
        .insert({"user_id": user_id, "title": "Async Note", "content": "Created async"})
        .execute()
    ).data[0]

    # Read
    notes = (await client.table("notes").select("*").execute()).data

    # Update
    updated = (
        await client.table("notes")
        .update({"title": "Updated Async"})
        .eq("id", note["id"])
        .execute()
    ).data[0]

    # Delete
    await client.table("notes").delete().eq("id", note["id"]).execute()


if __name__ == "__main__":
    asyncio.run(main())
