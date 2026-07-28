"""
Database layer with dual-backend support.
- SQLite (dev): used when DATABASE_URL is empty or unset
- PostgreSQL (production): used when DATABASE_URL starts with 'postgresql://'

Both backends expose the same interface via get_db(), so app/auth.py
and other callers don't need to know which engine is active.
"""
import os
import re
import sqlite3
import logging

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
USE_POSTGRES = DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://")

# ─── SQLite path (dev) ───
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "astrovakta.db")
_db_connection: sqlite3.Connection | None = None


# ═══════════════════════════════════════════════════════════
#  PostgreSQL Adapter
# ═══════════════════════════════════════════════════════════

_pg_pool = None

def _get_pg_pool():
    global _pg_pool
    if _pg_pool is None:
        import psycopg
        from psycopg.rows import dict_row
        _pg_pool = psycopg.ConnectionPool(
            conninfo=DATABASE_URL,
            min_size=2,
            max_size=10,
            row_factory=dict_row,
        )
        logger.info("PostgreSQL connection pool created")
    return _pg_pool


class PGCursorWrapper:
    """Wraps a psycopg cursor so it behaves like sqlite3 cursor + connection."""
    def __init__(self, pool):
        self._pool = pool
        self._conn = None
        self._cur = None

    def __enter__(self):
        self._conn = self._pool.getconn()
        self._cur = self._conn.cursor()
        return self

    def __exit__(self, *exc):
        if self._cur:
            self._cur.close()
        if self._conn:
            self._pool.putconn(self._conn)

    def execute(self, sql: str, params=None):
        """Auto-convert ? placeholders to %s for psycopg."""
        if params is not None and "?" in sql:
            sql = sql.replace("?", "%s")
        # Handle INSERT ... RETURNING id for lastrowid compatibility
        if self._cur is None:
            self._conn = self._pool.getconn()
            self._cur = self._conn.cursor()
        self._cur.execute(sql, params)
        return self._cur

    @property
    def lastrowid(self):
        """Emulate lastrowid — only valid right after an INSERT."""
        # psycopg3 doesn't have lastrowid; caller should use RETURNING instead.
        # Fallback: return None (callers that need it use RETURNING now).
        return None

    @property
    def rowcount(self):
        return self._cur.rowcount if self._cur else -1

    def fetchone(self):
        return self._cur.fetchone() if self._cur else None

    def fetchall(self):
        return self._cur.fetchall() if self._cur else []


class PGConnectionWrapper:
    """Mimics sqlite3.Connection: execute(), commit(), cursor()."""
    def __init__(self):
        self._pool = _get_pg_pool()

    def execute(self, sql: str, params=None):
        if params is not None and "?" in sql:
            sql = sql.replace("?", "%s")
        conn = self._pool.getconn()
        cur = conn.cursor()
        cur.execute(sql, params)
        # Store conn+cur so commit() can access them
        self._active_conn = conn
        self._active_cur = cur
        return cur

    def commit(self):
        if self._active_conn:
            self._active_conn.commit()
            self._pool.putconn(self._active_conn)
            self._active_conn = None
            self._active_cur = None

    def cursor(self):
        return self

    @property
    def row_factory(self):
        return None

    @row_factory.setter
    def row_factory(self, val):
        pass  # psycopg always uses dict_row via pool config

    def executescript(self, script: str):
        """Execute multiple statements (DDL)."""
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(script)
            conn.commit()
        finally:
            self._pool.putconn(conn)


# ═══════════════════════════════════════════════════════════
#  Unified accessor
# ═══════════════════════════════════════════════════════════

def get_db():
    """Return a DB connection (SQLite or PG wrapper) matching the DATABASE_URL env."""
    if USE_POSTGRES:
        return PGConnectionWrapper()
    global _db_connection
    if _db_connection is None:
        _db_connection = sqlite3.connect(DB_PATH, check_same_thread=False)
        _db_connection.row_factory = sqlite3.Row
        _db_connection.execute("PRAGMA journal_mode=WAL")
        _db_connection.execute("PRAGMA foreign_keys=ON")
    return _db_connection


# ═══════════════════════════════════════════════════════════
#  Schema DDL
# ═══════════════════════════════════════════════════════════

_SQLITE_DDL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    plan TEXT DEFAULT 'free',
    is_admin BOOLEAN DEFAULT 0,
    avatar_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    key TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    tier TEXT DEFAULT 'free',
    rate_limit INTEGER DEFAULT 100,
    request_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS usage_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_key_id INTEGER NOT NULL,
    endpoint TEXT NOT NULL,
    status_code INTEGER,
    response_time_ms INTEGER,
    endpoint_group TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (api_key_id) REFERENCES api_keys(id)
);
CREATE TABLE IF NOT EXISTS ai_providers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    provider TEXT NOT NULL,
    api_key_encrypted TEXT NOT NULL,
    model TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS background_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    celery_task_id TEXT,
    job_type TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    input_data TEXT,
    result_data TEXT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS job_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    result_type TEXT,
    result_blob BLOB,
    file_size INTEGER,
    filename TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES background_jobs(id)
);
"""

_PG_DDL = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    plan TEXT DEFAULT 'free',
    is_admin BOOLEAN DEFAULT FALSE,
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    key TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    tier TEXT DEFAULT 'free',
    rate_limit INTEGER DEFAULT 100,
    request_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    revoked_at TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS usage_logs (
    id SERIAL PRIMARY KEY,
    api_key_id INTEGER NOT NULL REFERENCES api_keys(id),
    endpoint TEXT NOT NULL,
    status_code INTEGER,
    response_time_ms INTEGER,
    endpoint_group TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS ai_providers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    provider TEXT NOT NULL,
    api_key_encrypted TEXT NOT NULL,
    model TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS background_jobs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    celery_task_id TEXT,
    job_type TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    input_data TEXT,
    result_data TEXT,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS job_results (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES background_jobs(id),
    result_type TEXT,
    result_blob BYTEA,
    file_size INTEGER,
    filename TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
"""


def _migrate_sqlite(cursor, table, column, col_type):
    try:
        existing = cursor.execute(f"PRAGMA table_info({table})").fetchall()
        col_names = [row[1] for row in existing]
        if column not in col_names:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
    except Exception:
        pass


def _migrate_pg(pool, table, column, col_type):
    try:
        conn = pool.getconn()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = %s AND column_name = %s",
                (table, column),
            )
            if not cur.fetchone():
                cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        conn.commit()
        pool.putconn(conn)
    except Exception as e:
        logger.debug(f"Migration {table}.{column}: {e}")


def init_db() -> None:
    if USE_POSTGRES:
        pool = _get_pg_pool()
        conn = pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(_PG_DDL)
            conn.commit()
        finally:
            pool.putconn(conn)
        for t, c, ct in [
            ("users", "is_admin", "BOOLEAN DEFAULT FALSE"),
            ("users", "avatar_url", "TEXT"),
            ("usage_logs", "response_time_ms", "INTEGER"),
            ("usage_logs", "endpoint_group", "TEXT"),
        ]:
            _migrate_pg(pool, t, c, ct)
        logger.info("PostgreSQL schema initialized")
    else:
        conn = get_db()
        cursor = conn.cursor()
        cursor.executescript(_SQLITE_DDL)
        _migrate_sqlite(cursor, "users", "is_admin", "BOOLEAN DEFAULT 0")
        _migrate_sqlite(cursor, "users", "avatar_url", "TEXT")
        _migrate_sqlite(cursor, "usage_logs", "response_time_ms", "INTEGER")
        _migrate_sqlite(cursor, "usage_logs", "endpoint_group", "TEXT")
        conn.commit()