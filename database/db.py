import sqlite3
from settings import FIRST_BALANCE


conn = sqlite3.connect("database/bot.db", check_same_thread=False)
cursor = conn.cursor()

# Jadval yaratish
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    Name TEXT,
    username TEXT,
    stage TEXT,
    user_index INTEGER,
    balance FLOAT DEFAULT 0
)
""")

conn.commit()


def get(table, user_id=None):

    if table != "users":
        return None

    if user_id is None:
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()

        users = []
        for r in rows:
            users.append({
                "user_id": r[0],
                "Name": r[1],
                "username": r[2],
                "stage": r[3],
                "index": r[4]
            })

        return users

    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    r = cursor.fetchone()

    if not r:
        return None

    return {
        "user_id": r[0],
        "Name": r[1],
        "username": r[2],
        "stage": r[3],
        "index": r[4]
    }


def insert(table, data, user_id=None):
    if table != "users":
        return

    cursor.execute("""
    INSERT INTO users (user_id, Name, username, stage, user_index, balance)
    VALUES (?, ?, ?, ?, ?, ?)
    ON CONFLICT(user_id) DO UPDATE SET
        Name=excluded.Name,
        username=excluded.username,
        stage=excluded.stage,
        user_index=excluded.user_index
    """, (
        user_id,
        data.get("Name"),
        data.get("username"),
        data.get("stage"),
        data.get("index"),
        FIRST_BALANCE
    ))

    conn.commit()


def upd(table, data, user_id=None):

    if table != "users":
        return

    cursor.execute("""
    UPDATE users
    SET Name=?, username=?, stage=?, user_index=?
    WHERE user_id=?
    """, (
        data.get("Name"),
        data.get("username"),
        data.get("stage"),
        data.get("index"),
        user_id
    ))

    conn.commit()


def delete(table, user_id=None):

    if table != "users":
        return

    cursor.execute("DELETE FROM users WHERE user_id=?", (user_id,))
    conn.commit()