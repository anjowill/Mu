import sqlite3

conn = sqlite3.connect("app/database/users.db")
cursor = conn.cursor()

# Check columns
cursor.execute("PRAGMA table_info(users);")
columns = cursor.fetchall()

print("COLUMNS:")
for col in columns:
    print(col[1])

# Check users
cursor.execute("SELECT username, is_admin FROM users;")
rows = cursor.fetchall()

print("\nUSERS:")
print(rows)

cursor.execute("SELECT id, username, email, status FROM pending_users;")
rows = cursor.fetchall()
print("\nPENDING USERS:")
for r in rows:
    print(r)

conn.close()