import sqlite3

conn = sqlite3.connect('sensai.db')
cursor = conn.cursor()

# Check existing tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Available tables:", [t[0] for t in tables])

conn.close()
