import sqlite3
import os

# Get the correct database path
data_root_dir = "db"
sqlite_db_path = f"{data_root_dir}/db.sqlite"

print(f"Database path: {sqlite_db_path}")

conn = sqlite3.connect(sqlite_db_path)
cursor = conn.cursor()

try:
    # Add the missing last_activity column with proper handling
    cursor.execute("ALTER TABLE posts ADD COLUMN last_activity TEXT")
    print("✓ Added last_activity column to posts table")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("✓ last_activity column already exists")
    else:
        print(f"✗ Error adding column: {e}")

# Update existing posts to have last_activity = created_at
cursor.execute("UPDATE posts SET last_activity = created_at WHERE last_activity IS NULL")
print("✓ Updated existing posts with last_activity timestamps")

conn.commit()
conn.close()
print("🎉 Database schema fix completed!")
