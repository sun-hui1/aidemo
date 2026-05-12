# view_db.py
import sqlite3

conn = sqlite3.connect('agent_memory.db')
cursor = conn.cursor()

print("=== 表名 ===")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
for row in cursor.fetchall():
    print(row[0])

print("\n=== 第一张表前25行 ===")
tables = [row[0] for row in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
if tables:
    table = tables[0]
    cursor.execute(f"SELECT * FROM {table} LIMIT 25;")
    rows = cursor.fetchall()
    for row in rows:
        print(row)

conn.close()