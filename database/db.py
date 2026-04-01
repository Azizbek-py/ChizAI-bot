import sqlite3
import json

FIRST_BALANCE = 10000

conn = sqlite3.connect("database/bot.db", check_same_thread=False)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# ================= USERS =================
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


# ================= TEMPLATES =================
cursor.execute("""
CREATE TABLE IF NOT EXISTS templates (
    id INTEGER PRIMARY KEY,
    file_id TEXT,
    name TEXT,
    price FLOAT DEFAULT 0,
    prompt TEXT,
    author_id INTEGER,
    created_at TEXT DEFAULT (datetime('now'))
)
""")
conn.commit()

cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_templates_file_id ON templates(file_id)")
conn.commit()


# ================= UTILS =================
def _ensure_saved_struct(s):
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
    if isinstance(s, str):
        try:
            s = json.loads(s)
        except:
            return []
    if not isinstance(s, list):
        return []
    return s


# ================= USERS CRUD =================
def get(table, user_id=None):
    if table != "users":
        return None

    cursor.execute("SELECT * FROM users" if user_id is None else "SELECT * FROM users WHERE user_id=?", (() if user_id is None else (user_id,)))
    rows = cursor.fetchall()

    def parse(r):
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

    if user_id is None:
        return [parse(r) for r in rows]

    return parse(rows[0]) if rows else None


def insert(table, data, user_id=None):
    if table != "users":
        return

    exists = get("users", user_id)

    saved = _ensure_saved_struct(data.get("saved", {}))
    caches = _ensure_list(data.get("caches", []))

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
            json.dumps(saved),
            json.dumps(caches),
            data.get("uniq_id", 0)
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
            json.dumps(saved),
            json.dumps(caches),
            data.get("uniq_id", exists["uniq_id"]),
            user_id
        ))

    conn.commit()


def upd(table, data, user_id=None):
    if table != "users":
        return

    old = get("users", user_id)
    if not old:
        return

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
        json.dumps(data.get("saved", old["saved"])),
        json.dumps(data.get("caches", old["caches"])),
        data.get("uniq_id", old["uniq_id"]),
        user_id
    ))

    conn.commit()


def add_saved_item(user_id, file_id, prompt, amount):
    u = get("users", user_id)
    if not u:
        return

    s = u["saved"]
    s["items"] = [x for x in s["items"] if x["file_id"] != file_id]

    s["items"].append({
        "file_id": file_id,
        "prompt": prompt,
        "amount": amount
    })

    upd("users", {"saved": s}, user_id)


def add_cache(user_id, value):
    u = get("users", user_id)
    if not u:
        return

    c = u["caches"]
    c.append(value)

    upd("users", {"caches": c}, user_id)


def delete(table, user_id=None, file_id=None):
    if table != "users":
        return

    if file_id:
        u = get("users", user_id)
        if not u:
            return

        s = u["saved"]
        s["items"] = [x for x in s["items"] if x["file_id"] != file_id]

        upd("users", {"saved": s}, user_id)
        return

    cursor.execute("DELETE FROM users WHERE user_id=?", (user_id,))
    conn.commit()


# ================= TEMPLATES CRUD =================
def prompt_get(table, id=None):
    if table != "templates":
        return None

    if id is None:
        cursor.execute("SELECT * FROM templates ORDER BY id ASC")
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

    cursor.execute("SELECT * FROM templates WHERE id=?", (id,))
    r = cursor.fetchone()
    return dict(r) if r else None


def prompt_insert(table, data, id=None):
    if table != "templates":
        return

    file_id = (data.get("file_id") or "").strip()

    if file_id:
        cursor.execute("SELECT 1 FROM templates WHERE file_id=?", (file_id,))
        if cursor.fetchone():
            return

    cursor.execute("""
    INSERT INTO templates (id, file_id, name, price, prompt, author_id)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        id,
        file_id,
        data.get("name"),
        data.get("price", 0),
        data.get("prompt"),
        data.get("author_id")
    ))

    conn.commit()


def prompt_upd(table, data, id):
    if table != "templates":
        return

    old = prompt_get("templates", id)
    if not old:
        return

    cursor.execute("""
    UPDATE templates
    SET file_id=?, name=?, price=?, prompt=?, author_id=?
    WHERE id=?
    """, (
        data.get("file_id", old["file_id"]),
        data.get("name", old["name"]),
        data.get("price", old["price"]),
        data.get("prompt", old["prompt"]),
        data.get("author_id", old["author_id"]),
        id
    ))

    conn.commit()


def prompt_delete(table, id=None):
    if table != "templates":
        return

    cursor.execute("DELETE FROM templates WHERE id=?", (id,))
    conn.commit()