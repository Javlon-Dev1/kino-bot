import aiosqlite
from datetime import datetime

from config import DB_PATH


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                joined_at TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER UNIQUE,
                title TEXT,
                invite_link TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE,
                title TEXT,
                file_id TEXT,
                views INTEGER DEFAULT 0,
                added_by INTEGER,
                status TEXT DEFAULT 'approved',
                created_at TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT,
                file_id TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                movie_code TEXT
            )
        """)
        await db.commit()


# ---------- users ----------

async def add_user(user_id: int, username: str | None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, joined_at) VALUES (?, ?, ?)",
            (user_id, username, datetime.utcnow().isoformat()),
        )
        await db.commit()


async def get_users_count() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM users")
        row = await cur.fetchone()
        return row[0]


# ---------- channels (majburiy obuna) ----------

async def add_channel(chat_id: int, title: str, invite_link: str | None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO channels (chat_id, title, invite_link) VALUES (?, ?, ?)",
            (chat_id, title, invite_link),
        )
        await db.commit()


async def remove_channel(chat_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM channels WHERE chat_id = ?", (chat_id,))
        await db.commit()


async def get_channels() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM channels")
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


# ---------- movies ----------

async def generate_next_code() -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM movies")
        row = await cur.fetchone()
        return str(1000 + row[0] + 1)


async def add_movie(code: str, title: str, file_id: str, added_by: int, status: str = "approved") -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO movies (code, title, file_id, added_by, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (code, title, file_id, added_by, status, datetime.utcnow().isoformat()),
        )
        await db.commit()
        return cur.lastrowid


async def get_movie_by_code(code: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM movies WHERE code = ? AND status = 'approved'", (code,)
        )
        row = await cur.fetchone()
        return dict(row) if row else None


async def search_movies_by_title(query: str, limit: int = 10) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM movies WHERE status = 'approved' AND title LIKE ? LIMIT ?",
            (f"%{query}%", limit),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def remove_movie(code: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("DELETE FROM movies WHERE code = ?", (code,))
        await db.commit()
        return cur.rowcount > 0


async def increment_views(movie_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE movies SET views = views + 1 WHERE id = ?", (movie_id,))
        await db.commit()


async def get_top_movies(limit: int = 10) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM movies WHERE status = 'approved' ORDER BY views DESC LIMIT ?",
            (limit,),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def get_movies_count() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM movies WHERE status = 'approved'")
        row = await cur.fetchone()
        return row[0]


# ---------- submissions (foydalanuvchi takliflari) ----------

async def add_submission(user_id: int, title: str, file_id: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO submissions (user_id, title, file_id, status, created_at) VALUES (?, ?, ?, 'pending', ?)",
            (user_id, title, file_id, datetime.utcnow().isoformat()),
        )
        await db.commit()
        return cur.lastrowid


async def get_pending_submissions() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM submissions WHERE status = 'pending'")
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def get_submission(submission_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM submissions WHERE id = ?", (submission_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def update_submission_status(submission_id: int, status: str, movie_code: str | None = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE submissions SET status = ?, movie_code = ? WHERE id = ?",
            (status, movie_code, submission_id),
        )
        await db.commit()


async def get_user_submissions(user_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM submissions WHERE user_id = ? ORDER BY id DESC", (user_id,)
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]
