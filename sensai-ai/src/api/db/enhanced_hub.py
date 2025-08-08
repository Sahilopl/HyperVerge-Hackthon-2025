"""
Extended database operations for enhanced Learning Hubs & Forums.
"""
import json
import asyncio
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from api.utils.db import execute_db_operation, get_new_db_connection
from api.config import (
    hubs_table_name, posts_table_name, users_table_name, post_votes_table_name,
    user_reputation_table_name, post_reports_table_name, moderation_actions_table_name,
    post_task_links_table_name, post_skill_links_table_name, post_badge_links_table_name,
    user_follows_table_name, hub_subscriptions_table_name, poll_options_table_name,
    poll_votes_table_name, post_tags_table_name
)
from api.utils.ai_moderation import get_ai_moderator
import logging

logger = logging.getLogger(__name__)

# User Reputation Management
async def get_user_reputation(user_id: int, hub_id: Optional[int] = None) -> Dict[str, int]:
    """Get user reputation score and breakdown."""
    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()
        
        if hub_id:
            await cursor.execute(
                f"SELECT score, helpful_answers, accepted_answers, upvotes_received, downvotes_received, posts_created FROM {user_reputation_table_name} WHERE user_id = ? AND hub_id = ?",
                (user_id, hub_id)
            )
        else:
            # Global reputation (aggregate across all hubs)
            await cursor.execute(
                f"SELECT SUM(score), SUM(helpful_answers), SUM(accepted_answers), SUM(upvotes_received), SUM(downvotes_received), SUM(posts_created) FROM {user_reputation_table_name} WHERE user_id = ?",
                (user_id,)
            )
        
        result = await cursor.fetchone()
        if not result or result[0] is None:
            return {"score": 0, "helpful_answers": 0, "accepted_answers": 0, "upvotes_received": 0, "downvotes_received": 0, "posts_created": 0}
        
        return {
            "score": result[0] or 0,
            "helpful_answers": result[1] or 0,
            "accepted_answers": result[2] or 0,
            "upvotes_received": result[3] or 0,
            "downvotes_received": result[4] or 0,
            "posts_created": result[5] or 0
        }

async def update_user_reputation(user_id: int, hub_id: int, action: str, points: int = 0):
    """Update user reputation based on actions."""
    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()
        
        # Insert or update reputation record
        await cursor.execute(
            f"""INSERT INTO {user_reputation_table_name} (user_id, hub_id, score, {action})
                VALUES (?, ?, ?, 1)
                ON CONFLICT(user_id, hub_id) DO UPDATE SET
                score = score + ?, {action} = {action} + 1, last_updated = CURRENT_TIMESTAMP""",
            (user_id, hub_id, points, points)
        )
        await conn.commit()

# AI Moderation Integration
async def moderate_post_content(post_id: int, title: str, content: str, author_id: int, post_type: str) -> Dict[str, Any]:
    """Apply AI moderation to post content."""
    try:
        # Get author reputation for context
        author_reputation = await get_user_reputation(author_id)
        
        context = {
            "post_type": post_type,
            "author_reputation": author_reputation["score"]
        }
        
        # Run AI moderation
        moderation_result = await get_ai_moderator().moderate_content(content, title, context)
        
        # Apply moderation action
        if moderation_result.is_toxic or moderation_result.requires_human_review:
            await apply_moderation_action(
                post_id=post_id,
                moderator_id=None,  # AI moderator
                action_type=moderation_result.suggested_action,
                reason=moderation_result.explanation,
                is_ai_moderated=True,
                ai_confidence=1.0 - moderation_result.toxicity_score
            )
        
        return {
            "moderation_status": "flagged" if moderation_result.is_toxic else "approved",
            "ai_moderation_score": moderation_result.toxicity_score,
            "requires_human_review": moderation_result.requires_human_review,
            "explanation": moderation_result.explanation
        }
    
    except Exception as e:
        logger.error(f"AI moderation failed for post {post_id}: {e}")
        return {
            "moderation_status": "pending",
            "ai_moderation_score": None,
            "requires_human_review": True,
            "explanation": "Automatic moderation failed"
        }

# Enhanced Post Creation with AI Moderation
async def create_post_with_moderation(
    hub_id: int, user_id: int, title: Optional[str], content: str, post_type: str,
    parent_id: Optional[int] = None, poll_options: Optional[List[str]] = None,
    poll_duration_days: Optional[int] = None, allow_multiple_answers: Optional[bool] = None,
    category: Optional[str] = None, tags: Optional[List[str]] = None
) -> int:
    """Create a post with AI moderation and comprehensive features."""
    
    # Calculate poll expiration
    poll_expires_at = None
    if post_type == "poll" and poll_duration_days:
        poll_expires_at = datetime.now() + timedelta(days=poll_duration_days)
    
    # Insert the base post
    post_id = await execute_db_operation(
        f"""INSERT INTO {posts_table_name} 
           (hub_id, user_id, parent_id, title, content, post_type, poll_duration_days, 
            allow_multiple_answers, poll_expires_at, category, is_answered, accepted_answer_id,
            moderation_status, last_activity)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', CURRENT_TIMESTAMP)""",
        (hub_id, user_id, parent_id, title, content, post_type, poll_duration_days,
         allow_multiple_answers, poll_expires_at, category, 
         False if post_type == "question" else None,
         None),
        get_last_row_id=True
    )
    
    # Run AI moderation
    moderation_result = await moderate_post_content(post_id, title or "", content, user_id, post_type)
    
    # Update post with moderation results
    await execute_db_operation(
        f"UPDATE {posts_table_name} SET moderation_status = ?, ai_moderation_score = ? WHERE id = ?",
        (moderation_result["moderation_status"], moderation_result["ai_moderation_score"], post_id)
    )
    
    # Create poll options if it's a poll
    if post_type == "poll" and poll_options:
        for i, option_text in enumerate(poll_options):
            await execute_db_operation(
                f"INSERT INTO {poll_options_table_name} (post_id, option_text, option_order) VALUES (?, ?, ?)",
                (post_id, option_text, i)
            )
    
    # Add tags for QnA
    if tags:
        for tag in tags:
            await execute_db_operation(
                f"INSERT INTO {post_tags_table_name} (post_id, tag) VALUES (?, ?) ON CONFLICT DO NOTHING",
                (post_id, tag.lower().strip())
            )
    
    # Update user reputation
    await update_user_reputation(user_id, hub_id, "posts_created", points=5)
    
    # Update hub statistics
    await update_hub_stats(hub_id)
    
    return post_id

# Content Linking Functions
async def link_post_to_task(post_id: int, task_id: int):
    """Link a post to a task."""
    await execute_db_operation(
        f"INSERT INTO {post_task_links_table_name} (post_id, task_id) VALUES (?, ?) ON CONFLICT DO NOTHING",
        (post_id, task_id)
    )

async def link_post_to_skill(post_id: int, skill_name: str):
    """Link a post to a skill."""
    await execute_db_operation(
        f"INSERT INTO {post_skill_links_table_name} (post_id, skill_name) VALUES (?, ?) ON CONFLICT DO NOTHING",
        (post_id, skill_name.lower().strip())
    )

async def link_post_to_badge(post_id: int, badge_id: int):
    """Link a post to a badge."""
    await execute_db_operation(
        f"INSERT INTO {post_badge_links_table_name} (post_id, badge_id) VALUES (?, ?) ON CONFLICT DO NOTHING",
        (post_id, badge_id)
    )

async def get_post_links(post_id: int) -> Dict[str, List[Dict]]:
    """Get all links associated with a post."""
    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()
        
        # Get task links
        await cursor.execute(
            f"""SELECT t.id, t.name, t.description FROM {post_task_links_table_name} ptl
               JOIN tasks t ON ptl.task_id = t.id WHERE ptl.post_id = ?""",
            (post_id,)
        )
        tasks = [{"id": row[0], "name": row[1], "description": row[2]} for row in await cursor.fetchall()]
        
        # Get skill links
        await cursor.execute(
            f"SELECT skill_name FROM {post_skill_links_table_name} WHERE post_id = ?",
            (post_id,)
        )
        skills = [{"name": row[0]} for row in await cursor.fetchall()]
        
        # Get badge links
        await cursor.execute(
            f"""SELECT b.id, b.name, b.description FROM {post_badge_links_table_name} pbl
               JOIN badges b ON pbl.badge_id = b.id WHERE pbl.post_id = ?""",
            (post_id,)
        )
        badges = [{"id": row[0], "name": row[1], "description": row[2]} for row in await cursor.fetchall()]
        
        return {"tasks": tasks, "skills": skills, "badges": badges}

# Moderation Functions
async def apply_moderation_action(
    post_id: int, moderator_id: Optional[int], action_type: str, reason: str,
    is_ai_moderated: bool = False, ai_confidence: Optional[float] = None
):
    """Apply a moderation action to a post."""
    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()
        
        # Record the moderation action
        await cursor.execute(
            f"""INSERT INTO {moderation_actions_table_name} 
               (post_id, moderator_id, action_type, reason, is_ai_moderated, ai_confidence)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (post_id, moderator_id, action_type, reason, is_ai_moderated, ai_confidence)
        )
        
        # Update post status based on action
        if action_type in ["hide", "delete"]:
            await cursor.execute(
                f"UPDATE {posts_table_name} SET moderation_status = ? WHERE id = ?",
                (action_type + "d", post_id)
            )
        elif action_type == "approve":
            await cursor.execute(
                f"UPDATE {posts_table_name} SET moderation_status = 'approved' WHERE id = ?",
                (post_id,)
            )
        
        # Update moderator reputation if human moderator
        if moderator_id and not is_ai_moderated:
            # Get the post's hub_id
            await cursor.execute(f"SELECT hub_id FROM {posts_table_name} WHERE id = ?", (post_id,))
            hub_id = (await cursor.fetchone())[0]
            await update_user_reputation(moderator_id, hub_id, "moderator_actions", points=2)
        
        await conn.commit()

async def report_post(post_id: int, reporter_id: int, reason: str, description: Optional[str] = None):
    """Report a post for moderation."""
    return await execute_db_operation(
        f"""INSERT INTO {post_reports_table_name} (post_id, reporter_id, reason, description)
           VALUES (?, ?, ?, ?)""",
        (post_id, reporter_id, reason, description)
    )

# Advanced Search Functions
async def search_posts(
    query: str, hub_ids: Optional[List[int]] = None, post_types: Optional[List[str]] = None,
    tags: Optional[List[str]] = None, category: Optional[str] = None, 
    author_id: Optional[int] = None, date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None, sort_by: str = "relevance", limit: int = 20, offset: int = 0
) -> List[Dict[str, Any]]:
    """Advanced search with filtering and sorting - simplified version."""
    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()
        
        # Build a simplified query first - just basic search
        base_query = f"""
        SELECT p.id, p.hub_id, p.title, p.content, p.post_type, p.created_at,
               u.first_name || ' ' || COALESCE(u.last_name, '') as author,
               0 as votes, COALESCE(p.reply_count, 0) as reply_count, COALESCE(p.view_count, 0) as view_count,
               COALESCE(p.moderation_status, 'approved') as moderation_status, 
               p.category, 
               COALESCE(p.is_answered, 0) as is_answered
        FROM {posts_table_name} p
        JOIN {users_table_name} u ON p.user_id = u.id
        """
        
        conditions = ["1=1"]  # Start with always true condition
        params = []
        
        # Add search conditions
        if query:
            conditions.append("(p.title LIKE ? OR p.content LIKE ?)")
            search_term = f"%{query}%"
            params.extend([search_term, search_term])
        
        if hub_ids:
            conditions.append(f"p.hub_id IN ({','.join(['?'] * len(hub_ids))})")
            params.extend(hub_ids)
        
        if post_types:
            conditions.append(f"p.post_type IN ({','.join(['?'] * len(post_types))})")
            params.extend(post_types)
        
        if category:
            conditions.append("p.category = ?")
            params.append(category)
        
        if author_id:
            conditions.append("p.user_id = ?")
            params.append(author_id)
        
        if date_from:
            conditions.append("p.created_at >= ?")
            params.append(date_from.isoformat() if hasattr(date_from, 'isoformat') else str(date_from))
        
        if date_to:
            conditions.append("p.created_at <= ?")
            params.append(date_to.isoformat() if hasattr(date_to, 'isoformat') else str(date_to))
        
        # Skip tag filtering for now to avoid table issues
        # TODO: Add tag filtering when post_tags table is confirmed to exist
        
        # Combine conditions
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
        
        # Add sorting
        if sort_by == "date":
            base_query += " ORDER BY p.created_at DESC"
        elif sort_by == "votes":
            base_query += " ORDER BY votes DESC, p.created_at DESC"
        elif sort_by == "replies":
            base_query += " ORDER BY p.reply_count DESC, p.created_at DESC"
        else:  # relevance - basic implementation
            base_query += " ORDER BY p.reply_count DESC, p.created_at DESC"
        
        # Add pagination
        base_query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        await cursor.execute(base_query, params)
        results = await cursor.fetchall()
        
        posts = []
        for row in results:
            post = {
                "id": row[0], "hub_id": row[1], "title": row[2], "content": row[3],
                "post_type": row[4], "created_at": row[5], "author": row[6],
                "votes": row[7], "reply_count": row[8], "view_count": row[9],
                "moderation_status": row[10], "category": row[11], "is_answered": row[12]
            }
            posts.append(post)
        
        return posts

# Personalized Feed Functions
async def get_personalized_feed(user_id: int, feed_type: str = "recommended", limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
    """Get personalized feed based on user preferences and activity."""
    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()
        
        if feed_type == "following":
            # Posts from users the current user follows
            query = f"""
            SELECT DISTINCT p.id, p.hub_id, p.title, p.content, p.post_type, p.created_at,
                   u.first_name || ' ' || COALESCE(u.last_name, '') as author,
                   COALESCE(pv.vote_count, 0) as votes, p.reply_count
            FROM {posts_table_name} p
            JOIN {users_table_name} u ON p.user_id = u.id
            JOIN {user_follows_table_name} uf ON p.user_id = uf.following_id
            LEFT JOIN (
                SELECT post_id, SUM(CASE WHEN vote_type = 'up' THEN 1 WHEN vote_type = 'down' THEN -1 ELSE 0 END) as vote_count
                FROM {post_votes_table_name} GROUP BY post_id
            ) pv ON p.id = pv.post_id
            WHERE uf.follower_id = ? AND p.moderation_status = 'approved'
            ORDER BY p.created_at DESC LIMIT ? OFFSET ?
            """
            params = [user_id, limit, offset]
        
        elif feed_type == "subscribed_hubs":
            # Posts from subscribed hubs
            query = f"""
            SELECT DISTINCT p.id, p.hub_id, p.title, p.content, p.post_type, p.created_at,
                   u.first_name || ' ' || COALESCE(u.last_name, '') as author,
                   COALESCE(pv.vote_count, 0) as votes, p.reply_count
            FROM {posts_table_name} p
            JOIN {users_table_name} u ON p.user_id = u.id
            JOIN {hub_subscriptions_table_name} hs ON p.hub_id = hs.hub_id
            LEFT JOIN (
                SELECT post_id, SUM(CASE WHEN vote_type = 'up' THEN 1 WHEN vote_type = 'down' THEN -1 ELSE 0 END) as vote_count
                FROM {post_votes_table_name} GROUP BY post_id
            ) pv ON p.id = pv.post_id
            WHERE hs.user_id = ? AND p.moderation_status = 'approved'
            ORDER BY p.last_activity DESC LIMIT ? OFFSET ?
            """
            params = [user_id, limit, offset]
        
        elif feed_type == "trending":
            # Trending posts (high activity in last 24 hours)
            query = f"""
            SELECT p.id, p.hub_id, p.title, p.content, p.post_type, p.created_at,
                   u.first_name || ' ' || COALESCE(u.last_name, '') as author,
                   COALESCE(pv.vote_count, 0) as votes, p.reply_count,
                   (COALESCE(pv.vote_count, 0) + p.reply_count * 2) as trend_score
            FROM {posts_table_name} p
            JOIN {users_table_name} u ON p.user_id = u.id
            LEFT JOIN (
                SELECT post_id, SUM(CASE WHEN vote_type = 'up' THEN 1 WHEN vote_type = 'down' THEN -1 ELSE 0 END) as vote_count
                FROM {post_votes_table_name} WHERE created_at > datetime('now', '-1 day') GROUP BY post_id
            ) pv ON p.id = pv.post_id
            WHERE p.moderation_status = 'approved' AND p.created_at > datetime('now', '-3 days')
            ORDER BY trend_score DESC, p.created_at DESC LIMIT ? OFFSET ?
            """
            params = [limit, offset]
        
        else:  # recommended (default)
            # Basic recommendation: recent posts with good engagement
            query = f"""
            SELECT p.id, p.hub_id, p.title, p.content, p.post_type, p.created_at,
                   u.first_name || ' ' || COALESCE(u.last_name, '') as author,
                   COALESCE(pv.vote_count, 0) as votes, p.reply_count
            FROM {posts_table_name} p
            JOIN {users_table_name} u ON p.user_id = u.id
            LEFT JOIN (
                SELECT post_id, SUM(CASE WHEN vote_type = 'up' THEN 1 WHEN vote_type = 'down' THEN -1 ELSE 0 END) as vote_count
                FROM {post_votes_table_name} GROUP BY post_id
            ) pv ON p.id = pv.post_id
            WHERE p.moderation_status = 'approved'
            ORDER BY (COALESCE(pv.vote_count, 0) + p.reply_count) DESC, p.created_at DESC 
            LIMIT ? OFFSET ?
            """
            params = [limit, offset]
        
        await cursor.execute(query, params)
        results = await cursor.fetchall()
        
        return [
            {
                "id": row[0], "hub_id": row[1], "title": row[2], "content": row[3],
                "post_type": row[4], "created_at": row[5], "author": row[6],
                "votes": row[7], "reply_count": row[8]
            }
            for row in results
        ]

# Hub Statistics and Management
async def update_hub_stats(hub_id: int):
    """Update hub statistics (subscriber count, post count, etc.)."""
    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()
        
        # Get post count
        await cursor.execute(
            f"SELECT COUNT(*) FROM {posts_table_name} WHERE hub_id = ? AND moderation_status = 'approved'",
            (hub_id,)
        )
        post_count = (await cursor.fetchone())[0]
        
        # Get subscriber count
        await cursor.execute(
            f"SELECT COUNT(*) FROM {hub_subscriptions_table_name} WHERE hub_id = ?",
            (hub_id,)
        )
        subscriber_count = (await cursor.fetchone())[0]
        
        # Get activity today
        await cursor.execute(
            f"""SELECT COUNT(*) FROM {posts_table_name} 
               WHERE hub_id = ? AND created_at > datetime('now', '-1 day') AND moderation_status = 'approved'""",
            (hub_id,)
        )
        active_today = (await cursor.fetchone())[0]
        
        # Update hub
        await cursor.execute(
            f"""UPDATE {hubs_table_name} 
               SET post_count = ?, subscriber_count = ?, active_today = ?
               WHERE id = ?""",
            (post_count, subscriber_count, active_today, hub_id)
        )
        await conn.commit()

# User Follow/Subscribe Functions
async def follow_user(follower_id: int, following_id: int):
    """Follow a user."""
    await execute_db_operation(
        f"INSERT INTO {user_follows_table_name} (follower_id, following_id) VALUES (?, ?) ON CONFLICT DO NOTHING",
        (follower_id, following_id)
    )

async def unfollow_user(follower_id: int, following_id: int):
    """Unfollow a user."""
    await execute_db_operation(
        f"DELETE FROM {user_follows_table_name} WHERE follower_id = ? AND following_id = ?",
        (follower_id, following_id)
    )

async def subscribe_to_hub(user_id: int, hub_id: int, notification_preference: str = "all"):
    """Subscribe to a hub."""
    await execute_db_operation(
        f"INSERT INTO {hub_subscriptions_table_name} (user_id, hub_id, notification_preference) VALUES (?, ?, ?) ON CONFLICT DO NOTHING",
        (user_id, hub_id, notification_preference)
    )
    await update_hub_stats(hub_id)

async def unsubscribe_from_hub(user_id: int, hub_id: int):
    """Unsubscribe from a hub."""
    await execute_db_operation(
        f"DELETE FROM {hub_subscriptions_table_name} WHERE user_id = ? AND hub_id = ?",
        (user_id, hub_id)
    )
    await update_hub_stats(hub_id)


async def get_leaderboard(limit: int = 10, time_period: str = "all_time"):
    """Get user leaderboard based on reputation and activity."""
    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()
        
        # Time period filter (simplified for now)
        time_filter = ""
        if time_period == "month":
            time_filter = "WHERE p.created_at > datetime('now', '-1 month')"
        elif time_period == "week":
            time_filter = "WHERE p.created_at > datetime('now', '-1 week')"
        
        # Simplified query using only existing tables
        query = f"""
        SELECT u.id, u.first_name || ' ' || COALESCE(u.last_name, '') as name,
               COUNT(DISTINCT p.id) as post_count,
               COUNT(DISTINCT pv.id) as helpful_votes,
               (COUNT(DISTINCT p.id) * 10 + COUNT(DISTINCT pv.id) * 5) as reputation
        FROM {users_table_name} u
        LEFT JOIN {posts_table_name} p ON u.id = p.user_id
        LEFT JOIN {post_votes_table_name} pv ON p.id = pv.post_id AND pv.vote_type = 'up'
        {time_filter}
        GROUP BY u.id, u.first_name, u.last_name
        HAVING post_count > 0 OR helpful_votes > 0
        ORDER BY reputation DESC, post_count DESC
        LIMIT ?
        """
        
        await cursor.execute(query, (limit,))
        rows = await cursor.fetchall()
        
        leaderboard = []
        for i, row in enumerate(rows, 1):
            leaderboard.append({
                "rank": i,
                "user_id": row[0],
                "name": row[1],
                "post_count": row[2],
                "helpful_votes": row[3],
                "reputation": row[4]
            })
        
        return leaderboard


async def get_posts_by_hub(hub_id: int):
    """Get all posts for a specific hub."""
    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()
        
        query = f"""
        SELECT p.id, p.title, p.content, p.post_type, p.created_at, u.email as author,
               COALESCE(SUM(CASE WHEN pv.vote_type = 'up' THEN 1 WHEN pv.vote_type = 'down' THEN -1 ELSE 0 END), 0) as votes,
               COUNT(replies.id) as comment_count, p.category, p.is_answered, 
               p.poll_expires_at, p.allow_multiple_answers, p.hub_id
        FROM {posts_table_name} p
        JOIN {users_table_name} u ON p.user_id = u.id
        LEFT JOIN {post_votes_table_name} pv ON p.id = pv.post_id
        LEFT JOIN {posts_table_name} replies ON p.id = replies.parent_id
        WHERE p.hub_id = ? AND p.parent_id IS NULL
        GROUP BY p.id, p.title, p.content, p.post_type, p.created_at, u.email, p.category, p.is_answered, p.poll_expires_at, p.allow_multiple_answers, p.hub_id
        ORDER BY p.created_at DESC
        """
        
        await cursor.execute(query, (hub_id,))
        rows = await cursor.fetchall()
        
        posts = []
        for row in rows:
            posts.append({
                "id": row[0],
                "title": row[1],
                "content": row[2],
                "post_type": row[3],
                "created_at": row[4],
                "author": row[5],
                "votes": row[6],
                "comment_count": row[7],
                "category": row[8],
                "is_answered": row[9],
                "poll_expires_at": row[10],
                "allow_multiple_answers": row[11],
                "hub_id": row[12]
            })
        
        return posts
