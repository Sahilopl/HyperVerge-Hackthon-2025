#!/usr/bin/env python3
"""
Database migration script to add poll and QnA features to existing posts table.
"""
import asyncio
import sqlite3
import aiosqlite
from api.config import sqlite_db_path

async def migrate_database():
    """Add new tables and columns for poll and QnA features."""
    async with aiosqlite.connect(sqlite_db_path) as conn:
        cursor = await conn.cursor()
        
        # Get existing columns
        await cursor.execute("PRAGMA table_info(posts)")
        existing_columns = [col[1] for col in await cursor.fetchall()]
        print(f"Existing columns in posts table: {existing_columns}")
        
        # Add new columns to posts table if they don't exist
        new_columns = [
            ("poll_duration_days", "INTEGER"),
            ("allow_multiple_answers", "BOOLEAN DEFAULT FALSE"),
            ("poll_expires_at", "DATETIME"),
            ("category", "TEXT DEFAULT 'general'"),
            ("is_answered", "BOOLEAN DEFAULT FALSE"),
            ("accepted_answer_id", "INTEGER")
        ]
        
        for col_name, col_type in new_columns:
            if col_name not in existing_columns:
                try:
                    await cursor.execute(f"ALTER TABLE posts ADD COLUMN {col_name} {col_type}")
                    print(f"✓ Added column {col_name} to posts table")
                except Exception as e:
                    print(f"✗ Failed to add column {col_name}: {e}")
        
        # Create poll_options table
        await cursor.execute(
            """CREATE TABLE IF NOT EXISTS poll_options (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER NOT NULL,
                    option_text TEXT NOT NULL,
                    option_order INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
                )"""
        )
        await cursor.execute(
            """CREATE INDEX IF NOT EXISTS idx_poll_options_post_id ON poll_options (post_id)"""
        )
        print("✓ Created poll_options table")
        
        # Create poll_votes table
        await cursor.execute(
            """CREATE TABLE IF NOT EXISTS poll_votes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    option_id INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
                    FOREIGN KEY (option_id) REFERENCES poll_options(id) ON DELETE CASCADE
                )"""
        )
        await cursor.execute(
            """CREATE INDEX IF NOT EXISTS idx_poll_votes_post_id ON poll_votes (post_id)"""
        )
        await cursor.execute(
            """CREATE UNIQUE INDEX IF NOT EXISTS idx_poll_votes_unique ON poll_votes (post_id, user_id, option_id)"""
        )
        print("✓ Created poll_votes table")
        
        # Create post_tags table
        await cursor.execute(
            """CREATE TABLE IF NOT EXISTS post_tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER NOT NULL,
                    tag TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(post_id, tag),
                    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
                )"""
        )
        await cursor.execute(
            """CREATE INDEX IF NOT EXISTS idx_post_tags_post_id ON post_tags (post_id)"""
        )
        await cursor.execute(
            """CREATE INDEX IF NOT EXISTS idx_post_tags_tag ON post_tags (tag)"""
        )
        print("✓ Created post_tags table")
        
        await conn.commit()

async def main():
    """Run the migration."""
    print("Starting database migration for poll and QnA features...")
    print(f"Database path: {sqlite_db_path}")
    
    try:
        await migrate_database()
        print("\n🎉 Migration completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
