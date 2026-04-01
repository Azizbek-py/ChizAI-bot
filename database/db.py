import sqlite3
import json

FIRST_BALANCE = 10000

conn = sqlite3.connect("database/bot.db", check_same_thread=False)
conn.row_factory = sqlite3.Row
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
    caches TEXT DEFAULT '[]',
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

if "caches" not in cols:
    cursor.execute("ALTER TABLE users ADD COLUMN caches TEXT DEFAULT '[]'")
    conn.commit()


def _ensure_saved_struct(s):
    if s is None:
        s = {}
    if isinstance(s, str):
        try:
            s = json.loads(s)
        except:
            s = {}
    if not isinstance(s, dict):
        s = {}
    s.setdefault("items", [])
    return s


def _ensure_list(s):
    if s is None:
        return []
    if isinstance(s, str):
        try:
            s = json.loads(s)
        except:
            return []
    if not isinstance(s, list):
        return []
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
                "user_id": r["user_id"],
                "Name": r["Name"],
                "username": r["username"],
                "stage": r["stage"],
                "user_index": r["user_index"],
                "saved_index": r["saved_index"],
                "balance": r["balance"],
                "saved": _ensure_saved_struct(r["saved"]),
                "caches": _ensure_list(r["caches"]),
                "uniq_id": r["uniq_id"]
            })

        return users

    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    r = cursor.fetchone()

    if not r:
        return None

    return {
        "user_id": r["user_id"],
        "Name": r["Name"],
        "username": r["username"],
        "stage": r["stage"],
        "user_index": r["user_index"],
        "saved_index": r["saved_index"],
        "balance": r["balance"],
        "saved": _ensure_saved_struct(r["saved"]),
        "caches": _ensure_list(r["caches"]),
        "uniq_id": r["uniq_id"]
    }


def insert(table, data, user_id=None):
    if table != "users":
        return

    exists = get("users", user_id=user_id)

    saved = _ensure_saved_struct(data.get("saved", {}))
    caches = _ensure_list(data.get("caches", []))
    uniq_id = data.get("uniq_id", 0)

    if not exists:
        cursor.execute("""
        INSERT INTO users (user_id, Name, username, stage, user_index, saved_index, balance, saved, caches, uniq_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            data.get("Name"),
            data.get("username"),
            data.get("stage"),
            data.get("user_index", 0),
            data.get("saved_index", 0),
            FIRST_BALANCE,
            json.dumps(saved, ensure_ascii=False),
            json.dumps(caches, ensure_ascii=False),
            uniq_id
        ))
    else:
        cursor.execute("""
        UPDATE users
        SET Name=?, username=?, stage=?, user_index=?, saved_index=?, saved=?, caches=?, uniq_id=?
        WHERE user_id=?
        """, (
            data.get("Name", exists["Name"]),
            data.get("username", exists["username"]),
            data.get("stage", exists["stage"]),
            data.get("user_index", exists["user_index"]),
            data.get("saved_index", exists["saved_index"]),
            json.dumps(saved, ensure_ascii=False),
            json.dumps(caches, ensure_ascii=False),
            uniq_id if "uniq_id" in data else exists.get("uniq_id", 0),
            user_id
        ))

    conn.commit()


def upd(table, data, user_id=None):
    if table != "users":
        return

    old = get("users", user_id=user_id)
    if not old:
        return

    saved = old["saved"]
    caches = old["caches"]

    if "saved" in data:
        saved = _ensure_saved_struct(data["saved"])

    if "caches" in data:
        caches = _ensure_list(data["caches"])

    cursor.execute("""
    UPDATE users
    SET Name=?, username=?, stage=?, user_index=?, saved_index=?, balance=?, saved=?, caches=?, uniq_id=?
    WHERE user_id=?
    """, (
        data.get("Name", old["Name"]),
        data.get("username", old["username"]),
        data.get("stage", old["stage"]),
        data.get("user_index", old["user_index"]),
        data.get("saved_index", old["saved_index"]),
        data.get("balance", old["balance"]),
        json.dumps(saved, ensure_ascii=False),
        json.dumps(caches, ensure_ascii=False),
        data.get("uniq_id", old["uniq_id"]),
        user_id
    ))

    conn.commit()


def add_cache(user_id: int, value):
    u = get("users", user_id=user_id)
    if not u:
        return

    caches = u["caches"]
    caches.append(value)

    upd("users", {"caches": caches}, user_id=user_id)


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

def delete(table, user_id=None, file_id=None):
    if table != "users":
        return

    if file_id is not None:
        u = get("users", user_id=user_id)
        if not u:
            return

        s = _ensure_saved_struct(u["saved"])
        s["items"] = [x for x in s["items"] if x.get("file_id") != str(file_id)]

        upd("users", {"saved": s}, user_id=user_id)
        return

    cursor.execute("DELETE FROM users WHERE user_id=?", (user_id,))
    conn.commit()


def prompt_get(table, id=None):
    if table != "templates":
        return None

    if id is None:
        cursor.execute("""
        SELECT id, file_id, name, price, prompt, author_id, created_at
        FROM templates
        ORDER BY id ASC
        """)
        rows = cursor.fetchall()
        items = []
        for r in rows:
            items.append({
                "id": r[0],
                "file_id": r[1],
                "name": r[2],
                "price": r[3],
                "prompt": r[4],
                "author_id": r[5],
                "created_at": r[6],
            })
        return items

    cursor.execute("""
    SELECT id, file_id, name, price, prompt, author_id, created_at
    FROM templates
    WHERE id=?
    """, (id,))
    r = cursor.fetchone()
    if not r:
        return None

    return {
        "id": r[0],
        "file_id": r[1],
        "name": r[2],
        "price": r[3],
        "prompt": r[4],
        "author_id": r[5],
        "created_at": r[6],
    }


def prompt_insert(table, data, id=None):
    if table != "templates":
        return

    file_id = (data.get("file_id") or "").strip()

    if file_id != "":
        cursor.execute("SELECT 1 FROM templates WHERE file_id=? LIMIT 1", (file_id,))
        if cursor.fetchone():
            return

    cursor.execute("""
    INSERT INTO templates (id, file_id, name, price, prompt, author_id)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        id,
        file_id if file_id != "" else None,
        data.get("name"),
        data.get("price", 0.0),
        data.get("prompt"),
        data.get("author_id"),
    ))

    conn.commit()


def prompt_upd(table, data, id=None):
    if table != "templates":
        return

    old_data = prompt_get(table="templates", id=id)
    if not old_data:
        return

    new_file_id = (data.get("file_id") if "file_id" in data else old_data.get("file_id")) or ""
    new_file_id = str(new_file_id).strip()

    if new_file_id != "":
        cursor.execute("SELECT id FROM templates WHERE file_id=? LIMIT 1", (new_file_id,))
        row = cursor.fetchone()
        if row and int(row[0]) != int(id):
            return

    cursor.execute("""
    UPDATE templates
    SET file_id=?, name=?, price=?, prompt=?, author_id=?
    WHERE id=?
    """, (
        new_file_id if new_file_id != "" else None,
        data.get("name", old_data["name"]),
        data.get("price", old_data["price"]),
        data.get("prompt", old_data["prompt"]),
        data.get("author_id", old_data["author_id"]),
        id
    ))

    conn.commit()


def prompt_delete(table, id=None, file_id=None):
    if table != "templates":
        return

    if file_id is not None:
        fid = str(file_id).strip()
        cursor.execute("DELETE FROM templates WHERE file_id=?", (fid,))
        conn.commit()
        return

    cursor.execute("DELETE FROM templates WHERE id=?", (id,))
    conn.commit()