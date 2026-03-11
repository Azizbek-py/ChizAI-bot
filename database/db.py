import sqlite3
import json

FIRST_BALANCE = 2000

conn = sqlite3.connect("database/bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    Name TEXT,
    username TEXT,
    stage TEXT,
    user_index INTEGER,
    saved_index INTEGER,
    balance FLOAT DEFAULT 0,
    saved TEXT DEFAULT '{}',
    uniq_id INTEGER
)
""")
conn.commit()

cursor.execute("PRAGMA table_info(users)")
cols = {row[1] for row in cursor.fetchall()}
if "saved" not in cols:
    cursor.execute("ALTER TABLE users ADD COLUMN saved TEXT DEFAULT '{}'")
    conn.commit()
if "uniq_id" not in cols:
    cursor.execute("ALTER TABLE users ADD COLUMN uniq_id INTEGER")
    conn.commit()


def _ensure_saved_struct(s):
    if s is None:
        s = {}
    if isinstance(s, str):
        try:
            s = json.loads(s)
        except Exception:
            s = {}
    if not isinstance(s, dict):
        s = {}
    s.setdefault("items", [])
    if not isinstance(s["items"], list):
        s["items"] = []
    return s


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
                "user_index": r[4],
                "saved_index": r[5],
                "balance": r[6],
                "saved": _ensure_saved_struct(r[7]),
                "uniq_id": r[8]
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
        "user_index": r[4],
        "saved_index": r[5],
        "balance": r[6],
        "saved": _ensure_saved_struct(r[7]),
        "uniq_id": r[8]
    }


def insert(table, data, user_id=None):
    if table != "users":
        return

    exists = get(table="users", user_id=user_id)
    saved = _ensure_saved_struct(data.get("saved", {}))
    uniq_id = data.get("uniq_id", 0)

    if not exists:
        cursor.execute("""
        INSERT INTO users (user_id, Name, username, stage, user_index, saved_index, balance, saved, uniq_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            data.get("Name"),
            data.get("username"),
            data.get("stage"),
            data.get("user_index", 0),
            data.get("saved_index", 0),
            FIRST_BALANCE,
            json.dumps(saved, ensure_ascii=False),
            uniq_id
        ))
    else:
        old_saved = _ensure_saved_struct(exists.get("saved"))
        if "saved" not in data:
            saved = old_saved

        cursor.execute("""
        UPDATE users
        SET Name=?, username=?, stage=?, user_index=?, saved_index=?, saved=?, uniq_id=?
        WHERE user_id=?
        """, (
            data.get("Name", exists["Name"]),
            data.get("username", exists["username"]),
            data.get("stage", exists["stage"]),
            data.get("user_index", exists["user_index"]),
            data.get("saved_index", exists["saved_index"]),
            json.dumps(saved, ensure_ascii=False),
            uniq_id if "uniq_id" in data else exists.get("uniq_id", 0),
            user_id
        ))

    conn.commit()


def upd(table, data, user_id=None):
    if table != "users":
        return

    old_data = get(table="users", user_id=user_id)
    if not old_data:
        return

    saved = old_data.get("saved", {})
    if "saved" in data:
        saved = _ensure_saved_struct(data.get("saved"))

    cursor.execute("""
    UPDATE users
    SET Name=?, username=?, stage=?, user_index=?, saved_index=?, balance=?, saved=?, uniq_id=?
    WHERE user_id=?
    """, (
        data.get("Name", old_data["Name"]),
        data.get("username", old_data["username"]),
        data.get("stage", old_data["stage"]),
        data.get("user_index", old_data["user_index"]),
        data.get("saved_index", old_data["saved_index"]),
        data.get("balance", old_data["balance"]),
        json.dumps(saved, ensure_ascii=False),
        data.get("uniq_id", old_data.get("uniq_id", 0)),
        user_id
    ))

    conn.commit()


def add_saved_item(user_id: int, file_id: str, prompt: str, amount: float):
    u = get("users", user_id=user_id)
    if not u:
        return
    s = _ensure_saved_struct(u.get("saved"))
    item = {
        "file_id": str(file_id),
        "prompt": (prompt or "").strip(),
        "amount": float(amount),
    }
    s["items"] = [x for x in s["items"] if x.get("file_id") != str(file_id)]
    s["items"].append(item)
    upd("users", {"saved": s}, user_id=user_id)


def delete(table, user_id=None, file_id: str = None):
    if table != "users":
        return

    if file_id is not None and user_id is not None:
        u = get("users", user_id=user_id)
        if not u:
            return
        s = _ensure_saved_struct(u.get("saved"))
        fid = str(file_id)
        s["items"] = [x for x in s["items"] if x.get("file_id") != fid]
        upd("users", {"saved": s}, user_id=user_id)
        return

    cursor.execute("DELETE FROM users WHERE user_id=?", (user_id,))
    conn.commit()