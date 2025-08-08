#!/usr/bin/env python3
"""
Database migration script to add comprehensive Learning Hubs & Forums features.
"""
import asyncio
import aiosqlite
from api.config import sqlite_db_path

async def migrate_enhanced_forums():
    """Add all new tables and columns for the comprehensive forum system."""
    async with aiosqlite.connect(sqlite_db_path) as conn:
        cursor = await conn.cursor()
        
        # Add new columns to hubs table
        await cursor.execute("PRAGMA table_info(hubs)")
        hub_columns = [col[1] for col in await cursor.fetchall()]
        
        hub_new_columns = [
            ("subscriber_count", "INTEGER DEFAULT 0"),
            ("post_count", "INTEGER DEFAULT 0"),
            ("active_today", "INTEGER DEFAULT 0"),
            ("topics", "TEXT"),  # JSON array of topics
            ("moderators", "TEXT"),  # JSON array of moderator user IDs
            ("is_active", "BOOLEAN DEFAULT TRUE"),
            ("created_at", "DATETIME DEFAULT CURRENT_TIMESTAMP")
        ]
        
        for col_name, col_type in hub_new_columns:
            if col_name not in hub_columns:
                try:
                    await cursor.execute(f"ALTER TABLE hubs ADD COLUMN {col_name} {col_type}")
                    print(f"✓ Added column {col_name} to hubs table")
                except Exception as e:
                    print(f"✗ Failed to add column {col_name} to hubs: {e}")
        
        # Add new columns to posts table
        await cursor.execute("PRAGMA table_info(posts)")
        post_columns = [col[1] for col in await cursor.fetchall()]
        
        post_new_columns = [
            ("reply_count", "INTEGER DEFAULT 0"),
            ("view_count", "INTEGER DEFAULT 0"),
            ("moderation_status", "TEXT DEFAULT 'approved'"),  # approved, flagged, hidden, deleted
            ("ai_moderation_score", "REAL"),
            ("is_pinned", "BOOLEAN DEFAULT FALSE"),
            ("last_activity", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
            ("linked_tasks", "TEXT"),  # JSON array
            ("linked_skills", "TEXT"),  # JSON array
            ("linked_badges", "TEXT"),  # JSON array
        ]
        
        for col_name, col_type in post_new_columns:
            if col_name not in post_columns:
                try:
                    await cursor.execute(f"ALTER TABLE posts ADD COLUMN {col_name} {col_type}")
                    print(f"✓ Added column {col_name} to posts table")
                except Exception as e:
                    print(f"✗ Failed to add column {col_name} to posts: {e}")

        # Create user_reputation table
        await cursor.execute(
            """CREATE TABLE IF NOT EXISTS user_reputation (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    hub_id INTEGER,  -- NULL for global reputation
                    score INTEGER DEFAULT 0,
                    helpful_answers INTEGER DEFAULT 0,
                    accepted_answers INTEGER DEFAULT 0,
                    upvotes_received INTEGER DEFAULT 0,
                    downvotes_received INTEGER DEFAULT 0,
                    posts_created INTEGER DEFAULT 0,
                    moderator_actions INTEGER DEFAULT 0,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, hub_id),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (hub_id) REFERENCES hubs(id) ON DELETE CASCADE
                )"""
        )
        await cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_reputation_user_id ON user_reputation (user_id)")
        await cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_reputation_hub_id ON user_reputation (hub_id)")
        print("✓ Created user_reputation table")

        # Create post_reports table
        await cursor.execute(
            """CREATE TABLE IF NOT EXISTS post_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER NOT NULL,
                    reporter_id INTEGER NOT NULL,
                    reason TEXT NOT NULL CHECK (reason IN ('spam', 'harassment', 'inappropriate', 'misinformation', 'other')),
                    description TEXT,
                    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'reviewed', 'resolved', 'dismissed')),
                    reviewed_by INTEGER,
                    reviewed_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
                    FOREIGN KEY (reporter_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (reviewed_by) REFERENCES users(id) ON DELETE SET NULL
                )"""
        )
        await cursor.execute("CREATE INDEX IF NOT EXISTS idx_post_reports_post_id ON post_reports (post_id)")
        await cursor.execute("CREATE INDEX IF NOT EXISTS idx_post_reports_status ON post_reports (status)")
        print("✓ Created post_reports table")

        # Create moderation_actions table
        await cursor.execute(
            """CREATE TABLE IF NOT EXISTS moderation_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER NOT NULL,
                    moderator_id INTEGER NOT NULL,
                    action_type TEXT NOT NULL CHECK (action_type IN ('hide', 'delete', 'warn', 'ban', 'approve', 'flag')),
                    reason TEXT NOT NULL,
                    is_ai_moderated BOOLEAN DEFAULT FALSE,
                    ai_confidence REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
                    FOREIGN KEY (moderator_id) REFERENCES users(id) ON DELETE CASCADE
                )"""
        )
        await cursor.execute("CREATE INDEX IF NOT EXISTS idx_moderation_actions_post_id ON moderation_actions (post_id)")
        await cursor.execute("CREATE INDEX IF NOT EXISTS idx_moderation_actions_moderator ON moderation_actions (moderator_id)")
        print("✓ Created moderation_actions table")

        # Create post_task_links table
        await cursor.execute(
            """CREATE TABLE IF NOT EXISTS post_task_links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER NOT NULL,
                    task_id INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(post_id, task_id),
                    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
                    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
                )"""
        )
        await cursor.execute("CREATE INDEX IF NOT EXISTS idx_post_task_links_post_id ON post_task_links (post_id)")
        await cursor.execute("CREATE INDEX IF NOT EXISTS idx_post_task_links_task_id ON post_task_links (task_id)")
        print("✓ Created post_task_links table")

        # Create post_skill_links table
        await cursor.execute(
            """CREATE TABLE IF NOT EXISTS post_skill_links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER NOT NULL,
                    skill_name TEXT NOT NULL,  -- Since skills might not have dedicated table
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(post_id, skill_name),
                    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
                )"""
        )
        await cursor.execute("CREATE INDEX IF NOT EXISTS idx_post_skill_links_post_id ON post_skill_links (post_id)")
        await cursor.execute("CREATE INDEX IF NOT EXISTS idx_post_skill_links_skill ON post_skill_links (skill_name)")
        print("✓ Created post_skill_links table")

        # Create post_badge_links table
        await cursor.execute(
            """CREATE TABLE IF NOT EXISTS post_badge_links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER NOT NULL,
                    badge_id INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(post_id, badge_id),
                    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
                    FOREIGN KEY (badge_id) REFERENCES badges(id) ON DELETE CASCADE
                )"""
        )
        await cursor.execute("CREATE INDEX IF NOT EXISTS idx_post_badge_links_post_id ON post_badge_links (post_id)")
        await cursor.execute("CREATE INDEX IF NOT EXISTS idx_post_badge_links_badge_id ON post_badge_links (badge_id)")
        print("✓ Created post_badge_links table")

        # Create user_follows table
        await cursor.execute(
            """CREATE TABLE IF NOT EXISTS user_follows (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    follower_id INTEGER NOT NULL,
                    following_id INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(follower_id, following_id),
                    FOREIGN KEY (follower_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (following_id) REFERENCES users(id) ON DELETE CASCADE
                )"""
        )
        await cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_follows_follower ON user_follows (follower_id)")
        await cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_follows_following ON user_follows (following_id)")
        print("✓ Created user_follows table")

        # Create hub_subscriptions table
        await cursor.execute(
            """CREATE TABLE IF NOT EXISTS hub_subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    hub_id INTEGER NOT NULL,
                    notification_preference TEXT DEFAULT 'all' CHECK (notification_preference IN ('all', 'mentions', 'none')),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, hub_id),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (hub_id) REFERENCES hubs(id) ON DELETE CASCADE
                )"""
        )
        await cursor.execute("CREATE INDEX IF NOT EXISTS idx_hub_subscriptions_user_id ON hub_subscriptions (user_id)")
        await cursor.execute("CREATE INDEX IF NOT EXISTS idx_hub_subscriptions_hub_id ON hub_subscriptions (hub_id)")
        print("✓ Created hub_subscriptions table")

        await conn.commit()

async def main():
    """Run the enhanced forums migration."""
    print("Starting enhanced Learning Hubs & Forums migration...")
    print(f"Database path: {sqlite_db_path}")
    
    try:
        await migrate_enhanced_forums()
        print("\n🎉 Enhanced forums migration completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
