import os
import sqlite3

if os.path.exists("researchos.db"):
    conn = sqlite3.connect("researchos.db")
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    print(cur.fetchall())
else:
    print("researchos.db not found in current directory")
