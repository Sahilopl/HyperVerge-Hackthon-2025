# adityavofficial-hyperge-hackathon-2025/sensai-ai/src/api/db/hub.py

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from api.utils.db import execute_db_operation, get_new_db_connection
from api.config import (
    hubs_table_name,
    posts_table_name,
    users_table_name,
    post_votes_table_name,
    post_links_table_name
)

# Import new table names
from api.db import poll_options_table_name, poll_votes_table_name, post_tags_table_name

async def create_hub(org_id: int, name: str, description: Optional[str]) -> int:
    """
    Inserts a new hub into the database for a given organization.

    Args:
        org_id: The ID of the organization the hub belongs to.
        name: The name of the hub.
        description: A brief description of the hub.

    Returns:
        The ID of the newly created hub.
    """
    return await execute_db_operation(
        f"INSERT INTO {hubs_table_name} (org_id, name, description) VALUES (?, ?, ?)",
        (org_id, name, description),
        get_last_row_id=True
    )

async def get_hubs_by_org(org_id: int) -> List[Dict]:
    """
    Retrieves all hubs associated with a specific organization.

    Args:
        org_id: The ID of the organization.

    Returns:
        A list of dictionaries, each representing a hub.
    """
    rows = await execute_db_operation(
        f"SELECT id, name, description FROM {hubs_table_name} WHERE org_id = ? ORDER BY name ASC",
        (org_id,),
        fetch_all=True
    )
    return [{"id": row[0], "name": row[1], "description": row[2]} for row in rows]

async def delete_hub(hub_id: int):
    """Deletes a hub and all its associated posts and data."""
    await execute_db_operation(f"DELETE FROM {hubs_table_name} WHERE id = ?", (hub_id,))

async def delete_post(post_id: int):
    """Deletes a post or a comment."""
    await execute_db_operation(f"DELETE FROM {posts_table_name} WHERE id = ?", (post_id,))

async def create_post(
    hub_id: int, 
    user_id: int, 
    title: Optional[str], 
    content: str, 
    post_type: str, 
    parent_id: Optional[int] = None,
    # Poll-specific parameters
    poll_options: Optional[List[str]] = None,
    poll_duration_days: Optional[int] = None,
    allow_multiple_answers: Optional[bool] = None,
    # QnA-specific parameters
    category: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> int:
    """
    Creates a new post or a reply within a hub, with support for polls and QnA.

    Args:
        hub_id: The ID of the hub where the post is being created.
        user_id: The ID of the user creating the post.
        title: The title of the post (optional, for top-level posts).
        content: The main content of the post.
        post_type: The type of post (e.g., 'thread', 'question', 'reply', 'poll').
        parent_id: The ID of the parent post if this is a reply.
        poll_options: List of poll options (for poll posts).
        poll_duration_days: Duration of the poll in days.
        allow_multiple_answers: Whether users can select multiple options.
        category: Category for QnA posts.
        tags: List of tags for QnA posts.

    Returns:
        The ID of the newly created post.
    """
    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()
        
        try:
            # Calculate poll expiration if it's a poll
            poll_expires_at = None
            if post_type == 'poll' and poll_duration_days:
                poll_expires_at = datetime.now() + timedelta(days=poll_duration_days)
            
            # Create the main post
            await cursor.execute(
                f"""INSERT INTO {posts_table_name}
                   (hub_id, user_id, title, content, post_type, parent_id, 
                    poll_duration_days, allow_multiple_answers, poll_expires_at, category)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (hub_id, user_id, title, content, post_type, parent_id,
                 poll_duration_days, allow_multiple_answers, poll_expires_at, category)
            )
            
            post_id = cursor.lastrowid
            
            # Handle poll options
            if post_type == 'poll' and poll_options:
                for i, option in enumerate(poll_options):
                    await cursor.execute(
                        f"""INSERT INTO {poll_options_table_name}
                           (post_id, option_text, option_order) VALUES (?, ?, ?)""",
                        (post_id, option.strip(), i)
                    )
            
            # Handle QnA tags
            if tags:
                for tag in tags:
                    await cursor.execute(
                        f"""INSERT INTO {post_tags_table_name}
                           (post_id, tag) VALUES (?, ?)""",
                        (post_id, tag.strip().lower())
                    )
            
            await conn.commit()
            return post_id
            
        except Exception as e:
            await conn.rollback()
            raise e

async def get_posts_by_hub(hub_id: int) -> List[Dict]:
    """
    Retrieves all top-level posts for a specific hub, along with author, vote count, and type-specific data.

    Args:
        hub_id: The ID of the hub.

    Returns:
        A list of dictionaries, each representing a post.
    """
    query = f"""
        SELECT
            p.id, p.title, p.content, p.post_type, p.created_at, u.email as author,
            COALESCE(SUM(CASE WHEN pv.vote_type = 'up' THEN 1 WHEN pv.vote_type = 'down' THEN -1 ELSE 0 END), 0) as votes,
            (SELECT COUNT(*) FROM {posts_table_name} WHERE parent_id = p.id) as comment_count,
            p.category, p.is_answered, p.poll_expires_at, p.allow_multiple_answers
        FROM {posts_table_name} p
        JOIN {users_table_name} u ON p.user_id = u.id
        LEFT JOIN {post_votes_table_name} pv ON p.id = pv.post_id
        WHERE p.hub_id = ? AND p.parent_id IS NULL
        GROUP BY p.id, p.title, p.content, p.post_type, p.created_at, u.email, p.category, p.is_answered, p.poll_expires_at, p.allow_multiple_answers
        ORDER BY p.created_at DESC
    """
    rows = await execute_db_operation(query, (hub_id,), fetch_all=True)
    
    posts = []
    for row in rows:
        post = {
            "id": row[0], "title": row[1], "content": row[2], "post_type": row[3],
            "created_at": row[4], "author": row[5], "votes": int(row[6]), 
            "comment_count": row[7], "category": row[8], "is_answered": row[9],
            "poll_expires_at": row[10], "allow_multiple_answers": row[11]
        }
        
        # Add poll options and vote counts for poll posts
        if post["post_type"] == "poll":
            post["poll_options"] = await get_poll_options_with_votes(post["id"])
        
        # Add tags for QnA posts
        if post["post_type"] == "question":
            post["tags"] = await get_post_tags(post["id"])
            
        posts.append(post)
    
    return posts


async def get_post_with_details(post_id: int, user_id: Optional[int] = None) -> Optional[Dict]:
    post_query = f"""
        SELECT p.id, p.hub_id, p.title, p.content, p.post_type, p.created_at, u.email as author,
               COALESCE(SUM(CASE WHEN pv.vote_type = 'up' THEN 1 WHEN pv.vote_type = 'down' THEN -1 ELSE 0 END), 0) as votes,
               MAX(CASE WHEN pv.user_id = ? THEN pv.vote_type ELSE NULL END) as user_vote
        FROM {posts_table_name} p
        JOIN {users_table_name} u ON p.user_id = u.id
        LEFT JOIN {post_votes_table_name} pv ON p.id = pv.post_id
        WHERE p.id = ?
        GROUP BY p.id, p.hub_id, p.title, p.content, p.post_type, p.created_at, u.email
    """
    post_rows = await execute_db_operation(post_query, (user_id, post_id), fetch_all=True)
    if not post_rows:
        return None
    post_row = post_rows[0]

    comments_query = f"""
        SELECT p.id, p.content, p.created_at, u.email as author,
               COALESCE(SUM(CASE WHEN pv.vote_type = 'up' THEN 1 WHEN pv.vote_type = 'down' THEN -1 ELSE 0 END), 0) as votes,
               MAX(CASE WHEN pv.user_id = ? THEN pv.vote_type ELSE NULL END) as user_vote,
               p.hub_id, p.post_type
        FROM {posts_table_name} p
        JOIN {users_table_name} u ON p.user_id = u.id
        LEFT JOIN {post_votes_table_name} pv ON p.id = pv.post_id
        WHERE p.parent_id = ?
        GROUP BY p.id, p.content, p.created_at, u.email, p.hub_id, p.post_type
        ORDER BY p.created_at ASC
    """
    comment_rows = await execute_db_operation(comments_query, (user_id, post_id), fetch_all=True)

    post = {
        "id": post_row[0], "hub_id": post_row[1], "title": post_row[2], "content": post_row[3],
        "post_type": post_row[4], "created_at": post_row[5], "author": post_row[6],
        "votes": int(post_row[7]), "user_vote": post_row[8],
        "comments": [
            {
                "id": row[0], "content": row[1], "created_at": row[2], "author": row[3],
                "votes": int(row[4]), "user_vote": row[5], "hub_id": row[6], "post_type": row[7]
            } for row in comment_rows
        ]
    }
    return post


async def add_vote_to_post(post_id: int, user_id: int, vote_type: Optional[str], is_comment: bool):
    # If vote_type is None, it means the user is un-voting.
    if vote_type is None:
        await execute_db_operation(
            f"DELETE FROM {post_votes_table_name} WHERE post_id = ? AND user_id = ?",
            (post_id, user_id)
        )
    else:
        # Upsert the vote. This will insert a new vote or update an existing one.
        await execute_db_operation(
            f"""INSERT INTO {post_votes_table_name} (post_id, user_id, vote_type)
                VALUES (?, ?, ?)
                ON CONFLICT(post_id, user_id) DO UPDATE SET
                vote_type = excluded.vote_type""",
            (post_id, user_id, vote_type)
        )

async def add_link_to_post(post_id: int, item_type: str, item_id: int):
    """
    Links a post to another item in the system, like a task or course.

    Args:
        post_id: The ID of the post.
        item_type: The type of item to link (e.g., 'task', 'course').
        item_id: The ID of the item to link.
    """
    await execute_db_operation(
        f"INSERT INTO {post_links_table_name} (post_id, item_type, item_id) VALUES (?, ?, ?)",
        (post_id, item_type, item_id)
    )


async def get_poll_options_with_votes(post_id: int) -> List[Dict]:
    """
    Retrieves poll options with their vote counts for a poll post.

    Args:
        post_id: The ID of the poll post.

    Returns:
        A list of dictionaries containing option details and vote counts.
    """
    query = f"""
        SELECT po.id, po.option_text, po.option_order,
               COUNT(pv.id) as vote_count
        FROM {poll_options_table_name} po
        LEFT JOIN {poll_votes_table_name} pv ON po.id = pv.option_id
        WHERE po.post_id = ?
        GROUP BY po.id, po.option_text, po.option_order
        ORDER BY po.option_order
    """
    rows = await execute_db_operation(query, (post_id,), fetch_all=True)
    return [
        {
            "id": row[0],
            "text": row[1], 
            "order": row[2],
            "vote_count": row[3]
        } for row in rows
    ]


async def get_post_tags(post_id: int) -> List[str]:
    """
    Retrieves tags for a post.

    Args:
        post_id: The ID of the post.

    Returns:
        A list of tag strings.
    """
    rows = await execute_db_operation(
        f"SELECT tag FROM {post_tags_table_name} WHERE post_id = ? ORDER BY tag",
        (post_id,),
        fetch_all=True
    )
    return [row[0] for row in rows]


async def vote_on_poll(post_id: int, user_id: int, option_ids: List[int]):
    """
    Records user votes on a poll.

    Args:
        post_id: The ID of the poll post.
        user_id: The ID of the user voting.
        option_ids: List of option IDs the user is voting for.
    """
    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()
        
        try:
            # First, remove any existing votes by this user for this poll
            await cursor.execute(
                f"DELETE FROM {poll_votes_table_name} WHERE post_id = ? AND user_id = ?",
                (post_id, user_id)
            )
            
            # Add new votes
            for option_id in option_ids:
                await cursor.execute(
                    f"""INSERT INTO {poll_votes_table_name}
                       (post_id, user_id, option_id) VALUES (?, ?, ?)""",
                    (post_id, user_id, option_id)
                )
            
            await conn.commit()
            
        except Exception as e:
            await conn.rollback()
            raise e


async def get_user_poll_votes(post_id: int, user_id: int) -> List[int]:
    """
    Gets the option IDs that a user has voted for in a poll.

    Args:
        post_id: The ID of the poll post.
        user_id: The ID of the user.

    Returns:
        A list of option IDs the user voted for.
    """
    rows = await execute_db_operation(
        f"SELECT option_id FROM {poll_votes_table_name} WHERE post_id = ? AND user_id = ?",
        (post_id, user_id),
        fetch_all=True
    )
    return [row[0] for row in rows]