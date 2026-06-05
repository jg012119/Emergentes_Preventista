"""
Local SQLite-backed mock of the Supabase Python client.

When the real Supabase credentials are not configured, this module provides a
drop-in replacement that stores everything in a local SQLite file so the full
application can run without any cloud dependency.
"""

import re
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# ---------------------------------------------------------------------------
# Database file lives next to the backend package
# ---------------------------------------------------------------------------
DB_PATH = Path(__file__).resolve().parent.parent / "local.db"

# ---------------------------------------------------------------------------
# Schema & seed SQL (mirrors database/schema.sql)
# ---------------------------------------------------------------------------
_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    email       TEXT UNIQUE NOT NULL,
    phone       TEXT NOT NULL DEFAULT '',
    password_hash TEXT NOT NULL,
    role        TEXT NOT NULL DEFAULT 'client',
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS stores (
    id          TEXT PRIMARY KEY,
    user_id     TEXT REFERENCES users(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    address     TEXT NOT NULL DEFAULT '',
    latitude    REAL NOT NULL DEFAULT 0,
    longitude   REAL NOT NULL DEFAULT 0,
    phone       TEXT DEFAULT '',
    notes       TEXT DEFAULT '',
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS products (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    category    TEXT NOT NULL DEFAULT 'General',
    price       REAL NOT NULL DEFAULT 0,
    stock       INTEGER NOT NULL DEFAULT 0,
    active      INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS product_aliases (
    id                TEXT PRIMARY KEY,
    product_id        TEXT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    alias_text        TEXT NOT NULL,
    normalized_alias  TEXT NOT NULL,
    alias_type        TEXT DEFAULT 'user_phrase',
    confidence_weight REAL DEFAULT 1.00,
    is_active         INTEGER DEFAULT 1,
    created_at        TEXT DEFAULT (datetime('now')),
    UNIQUE (product_id, normalized_alias)
);

CREATE TABLE IF NOT EXISTS orders (
    id            TEXT PRIMARY KEY,
    user_id       TEXT REFERENCES users(id) ON DELETE CASCADE,
    store_id      TEXT REFERENCES stores(id) ON DELETE SET NULL,
    status        TEXT NOT NULL DEFAULT 'borrador',
    delivery_date TEXT,
    total         REAL NOT NULL DEFAULT 0,
    notes         TEXT DEFAULT '',
    nlp_data      JSON,
    created_at    TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS order_items (
    id          TEXT PRIMARY KEY,
    order_id    TEXT REFERENCES orders(id) ON DELETE CASCADE,
    product_id  TEXT REFERENCES products(id) ON DELETE SET NULL,
    quantity    INTEGER NOT NULL DEFAULT 1,
    unit_price  REAL NOT NULL DEFAULT 0,
    subtotal    REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id          TEXT PRIMARY KEY,
    user_id     TEXT REFERENCES users(id) ON DELETE CASCADE,
    order_id    TEXT REFERENCES orders(id) ON DELETE CASCADE,
    message     TEXT NOT NULL DEFAULT '',
    sender      TEXT NOT NULL DEFAULT 'user',
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS agent_feedback (
    id          TEXT PRIMARY KEY,
    user_id     TEXT REFERENCES users(id) ON DELETE CASCADE,
    message_id  TEXT NOT NULL REFERENCES chat_messages(id) ON DELETE CASCADE,
    order_id    TEXT REFERENCES orders(id) ON DELETE CASCADE,
    rating      TEXT NOT NULL CHECK (rating IN ('like', 'dislike')),
    comment     TEXT,
    context     JSON,
    created_at  TEXT DEFAULT (datetime('now')),
    updated_at  TEXT DEFAULT (datetime('now')),
    UNIQUE (user_id, message_id)
);

CREATE TABLE IF NOT EXISTS notifications (
    id          TEXT PRIMARY KEY,
    user_id     TEXT REFERENCES users(id) ON DELETE CASCADE,
    order_id    TEXT REFERENCES orders(id) ON DELETE CASCADE,
    type        TEXT NOT NULL DEFAULT 'chat',
    message     TEXT NOT NULL DEFAULT '',
    status      TEXT NOT NULL DEFAULT 'pendiente',
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS nlp_interactions (
    id                      TEXT PRIMARY KEY,
    user_id                 TEXT REFERENCES users(id) ON DELETE SET NULL,
    store_id                TEXT REFERENCES stores(id) ON DELETE SET NULL,
    raw_text                TEXT NOT NULL,
    normalized_text         TEXT,
    detected_intent         TEXT,
    extracted_json          JSON,
    confidence_score        REAL,
    validation_status       TEXT,
    requires_human_review   INTEGER DEFAULT 0,
    clarification_questions JSON,
    created_at              TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS nlp_corrections (
    id                   TEXT PRIMARY KEY,
    interaction_id       TEXT NOT NULL REFERENCES nlp_interactions(id) ON DELETE CASCADE,
    original_extraction  JSON NOT NULL,
    corrected_extraction JSON NOT NULL,
    correction_reason    TEXT,
    corrected_by         TEXT REFERENCES users(id) ON DELETE SET NULL,
    created_at           TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS clarification_events (
    id             TEXT PRIMARY KEY,
    interaction_id TEXT REFERENCES nlp_interactions(id) ON DELETE CASCADE,
    user_id        TEXT REFERENCES users(id) ON DELETE SET NULL,
    store_id       TEXT REFERENCES stores(id) ON DELETE SET NULL,
    question_type  TEXT NOT NULL,
    question_text  TEXT NOT NULL,
    options        JSON,
    answer_text    TEXT,
    resolved       INTEGER DEFAULT 0,
    created_at     TEXT DEFAULT (datetime('now'))
);
"""

# bcrypt hash for 'admin123'
_ADMIN_HASH = "$2b$12$w8vHrPmWbBxqzTKCP4aiuel1wIVaeCU/w1crvkZi3pOmyaxoLg6c."

_SEED_PRODUCTS = [
    ("Big Cola 3L", "Bebidas", 12.00, 200),
    ("Big Cola 2L", "Bebidas", 9.00, 300),
    ("Big Cola 1L", "Bebidas", 6.00, 400),
    ("Big Cola 500ml", "Bebidas", 4.00, 500),
    ("Coca-Cola 2L", "Bebidas", 14.00, 150),
    ("Coca-Cola 1L", "Bebidas", 10.00, 250),
    ("Coca-Cola 500ml", "Bebidas", 7.00, 350),
    ("Sporade 500ml", "Hidratantes", 8.00, 300),
    ("Sporade 1L", "Hidratantes", 12.00, 200),
    ("Cifrut 500ml", "Jugos", 5.00, 400),
    ("Cifrut 1L", "Jugos", 8.00, 250),
    ("Cifrut 2L", "Jugos", 12.00, 150),
    ("Volt 300ml", "Energizantes", 8.00, 200),
    ("Volt 500ml", "Energizantes", 12.00, 150),
    ("Agua Cielo 500ml", "Agua", 3.00, 600),
    ("Agua Cielo 1L", "Agua", 5.00, 400),
    ("Agua Cielo 2.5L", "Agua", 8.00, 200),
    ("Pulp 300ml", "Jugos", 5.00, 300),
    ("Pulp 1L", "Jugos", 9.00, 200),
    ("Oro 500ml", "Bebidas", 4.50, 300),
    ("Oro 2L", "Bebidas", 8.50, 220),
    ("Free Tea 500ml", "Té", 6.00, 250),
]

_SEED_ALIASES = [
    ("Big Cola 500ml", "big cola 500 ml", "big cola 500ml", "official", 1.00),
    ("Big Cola 500ml", "big chica", "big chica", "size_alias", 0.95),
    ("Big Cola 500ml", "big personal", "big personal", "size_alias", 0.95),
    ("Big Cola 500ml", "big chiquita", "big chiquita", "size_alias", 0.92),
    ("Big Cola 1L", "big cola 1 litro", "big cola 1l", "official", 1.00),
    ("Big Cola 1L", "big litro", "big litro", "size_alias", 1.00),
    ("Big Cola 2L", "big cola 2 litros", "big cola 2l", "official", 1.00),
    ("Big Cola 2L", "big cola 2lt", "big cola 2l", "official", 1.00),
    ("Big Cola 2L", "big dos litros", "big dos litros", "user_phrase", 1.00),
    ("Big Cola 2L", "big de dos", "big de dos", "user_phrase", 1.00),
    ("Big Cola 2L", "big de dos litros", "big de dos litros", "user_phrase", 1.00),
    ("Big Cola 2L", "big grande", "big grande", "size_alias", 0.93),
    ("Big Cola 2L", "big familiar", "big familiar", "size_alias", 0.97),
    ("Big Cola 2L", "bigg familiar", "bigg familiar", "typo_alias", 0.94),
    ("Big Cola 2L", "bik familiar", "bik familiar", "typo_alias", 0.88),
    ("Big Cola 2L", "big cola dos litrso", "big cola dos litrso", "typo_alias", 0.94),
    ("Big Cola 2L", "bigg cola 2 litros", "bigg cola 2l", "typo_alias", 0.94),
    ("Big Cola 2L", "cola familiar", "cola familiar", "size_alias", 0.96),
    ("Big Cola 2L", "cola grande", "cola grande", "size_alias", 0.90),
    ("Big Cola 3L", "big cola 3 litros", "big cola 3l", "official", 1.00),
    ("Big Cola 3L", "big tres litros", "big tres litros", "user_phrase", 1.00),
    ("Big Cola 3L", "big de tres", "big de tres", "user_phrase", 1.00),
    ("Big Cola 3L", "big super grande", "big super grande", "size_alias", 1.00),
    ("Agua Cielo 500ml", "cielo chica", "cielo chica", "size_alias", 1.00),
    ("Agua Cielo 500ml", "cielo chico", "cielo chico", "size_alias", 1.00),
    ("Agua Cielo 500ml", "cielo chika", "cielo chika", "typo_alias", 0.96),
    ("Agua Cielo 500ml", "sielo chica", "sielo chica", "typo_alias", 0.92),
    ("Agua Cielo 500ml", "cieelo chica", "cieelo chica", "typo_alias", 0.92),
    ("Agua Cielo 500ml", "cielito chico", "cielito chico", "cochabamba_slang", 0.98),
    ("Agua Cielo 500ml", "cielito", "cielito", "cochabamba_slang", 0.92),
    ("Agua Cielo 500ml", "cielo personal", "cielo personal", "size_alias", 0.98),
    ("Agua Cielo 500ml", "agua chica", "agua chica", "size_alias", 0.95),
    ("Agua Cielo 500ml", "agua personal", "agua personal", "size_alias", 0.95),
    ("Agua Cielo 500ml", "agua cielo chica", "agua cielo chica", "size_alias", 1.00),
    ("Agua Cielo 1L", "cielo 1 litro", "cielo 1l", "official", 1.00),
    ("Agua Cielo 1L", "cielo litro", "cielo litro", "size_alias", 1.00),
    ("Agua Cielo 2.5L", "cielo grande", "cielo grande", "size_alias", 0.95),
    ("Agua Cielo 2.5L", "agua grande", "agua grande", "size_alias", 0.93),
    ("Agua Cielo 2.5L", "cielo familiar", "cielo familiar", "size_alias", 0.92),
    ("Agua Cielo 2.5L", "agua cielo grande", "agua cielo grande", "size_alias", 0.95),
    ("Agua Cielo 2.5L", "cielo 2.5 litros", "cielo 2.5l", "official", 1.00),
    ("Volt 300ml", "volt lata", "volt lata", "unit_alias", 0.95),
    ("Volt 300ml", "lata de volt", "lata de volt", "unit_alias", 0.95),
    ("Volt 300ml", "votl lata", "votl lata", "typo_alias", 0.92),
    ("Volt 300ml", "vol lata", "vol lata", "typo_alias", 0.88),
    ("Volt 300ml", "bolt lata", "bolt lata", "typo_alias", 0.86),
    ("Volt 300ml", "voltcito", "voltcito", "cochabamba_slang", 0.95),
    ("Volt 300ml", "volt chico", "volt chico", "size_alias", 0.95),
    ("Volt 300ml", "caja de volt", "caja de volt", "unit_alias", 0.95),
    ("Volt 300ml", "cajita de volt", "cajita de volt", "unit_alias", 0.95),
    ("Volt 300ml", "cajas de volt", "cajas de volt", "unit_alias", 0.95),
    ("Volt 500ml", "volt grande", "volt grande", "size_alias", 0.92),
    ("Volt 500ml", "volt medio litro", "volt medio litro", "size_alias", 0.92),
    ("Pulp 300ml", "pulp chico", "pulp chico", "size_alias", 0.95),
    ("Pulp 300ml", "pulp chiquito", "pulp chiquito", "size_alias", 0.92),
    ("Pulp 300ml", "pulp chiko", "pulp chiko", "typo_alias", 0.92),
    ("Pulp 300ml", "pulpp chico", "pulpp chico", "typo_alias", 0.90),
    ("Pulp 300ml", "pulpito", "pulpito", "cochabamba_slang", 0.95),
    ("Pulp 300ml", "pulp mango chico", "pulp mango chico", "user_phrase", 0.85),
    ("Pulp 1L", "pulp litro", "pulp litro", "size_alias", 1.00),
    ("Cifrut 500ml", "cifrut chico", "cifrut chico", "size_alias", 0.95),
    ("Cifrut 500ml", "cifrut chiquito", "cifrut chiquito", "size_alias", 0.92),
    ("Cifrut 500ml", "cifrut chiko", "cifrut chiko", "typo_alias", 0.92),
    ("Cifrut 500ml", "cifru chico", "cifru chico", "typo_alias", 0.90),
    ("Cifrut 500ml", "cifruth chico", "cifruth chico", "typo_alias", 0.88),
    ("Cifrut 500ml", "cifrutcito", "cifrutcito", "cochabamba_slang", 0.95),
    ("Cifrut 1L", "cifrut litro", "cifrut litro", "size_alias", 1.00),
    ("Cifrut 1L", "cifrut de litro", "cifrut de litro", "size_alias", 1.00),
    ("Cifrut 2L", "cifrut grande", "cifrut grande", "size_alias", 0.95),
    ("Oro 500ml", "oro chico", "oro chico", "size_alias", 0.95),
    ("Oro 500ml", "orito", "orito", "cochabamba_slang", 0.95),
    ("Oro 2L", "oro grande", "oro grande", "size_alias", 0.95),
    ("Oro 2L", "oro grnade", "oro grnade", "typo_alias", 0.90),
    ("Oro 2L", "oro grand", "oro grand", "typo_alias", 0.88),
    ("Oro 2L", "oro 2 litros", "oro 2l", "official", 1.00),
    # Coca-Cola 500ml
    ("Coca-Cola 500ml", "coca", "coca", "user_phrase", 0.90),
    ("Coca-Cola 500ml", "coquita", "coquita", "user_phrase", 1.00),
    ("Coca-Cola 500ml", "gaseosa negra", "gaseosa negra", "user_phrase", 0.90),
    ("Coca-Cola 500ml", "refresco", "refresco", "user_phrase", 0.85),
    ("Coca-Cola 500ml", "coca chica", "coca chica", "size_alias", 0.95),
    ("Coca-Cola 500ml", "coca chiquita", "coca chiquita", "size_alias", 0.95),
    ("Coca-Cola 500ml", "coca personal", "coca personal", "size_alias", 0.95),
    # Coca-Cola 1L
    ("Coca-Cola 1L", "coca", "coca", "user_phrase", 0.90),
    ("Coca-Cola 1L", "gaseosa negra", "gaseosa negra", "user_phrase", 0.90),
    ("Coca-Cola 1L", "refresco", "refresco", "user_phrase", 0.85),
    ("Coca-Cola 1L", "coca de litro", "coca de litro", "size_alias", 1.00),
    # Coca-Cola 2L
    ("Coca-Cola 2L", "coca", "coca", "user_phrase", 0.90),
    ("Coca-Cola 2L", "gaseosa negra", "gaseosa negra", "user_phrase", 0.90),
    ("Coca-Cola 2L", "refresco", "refresco", "user_phrase", 0.85),
    ("Coca-Cola 2L", "coca grande", "coca grande", "size_alias", 0.95),
    ("Coca-Cola 2L", "coca familiar", "coca familiar", "size_alias", 0.95),
    # Agua Cielo 500ml
    ("Agua Cielo 500ml", "agua", "agua", "user_phrase", 0.90),
    ("Agua Cielo 500ml", "agüita", "aguita", "user_phrase", 1.00),
    ("Agua Cielo 500ml", "agua sin gas", "agua sin gas", "user_phrase", 0.95),
    ("Agua Cielo 500ml", "h2o", "h2o", "user_phrase", 0.90),
    ("Agua Cielo 500ml", "hidratación", "hidratacion", "user_phrase", 0.85),
    # Agua Cielo 1L
    ("Agua Cielo 1L", "agua", "agua", "user_phrase", 0.90),
    ("Agua Cielo 1L", "agüita", "aguita", "user_phrase", 0.95),
    ("Agua Cielo 1L", "agua sin gas", "agua sin gas", "user_phrase", 0.95),
    ("Agua Cielo 1L", "h2o", "h2o", "user_phrase", 0.90),
    ("Agua Cielo 1L", "hidratación", "hidratacion", "user_phrase", 0.85),
    # Agua Cielo 2.5L
    ("Agua Cielo 2.5L", "agua", "agua", "user_phrase", 0.90),
    ("Agua Cielo 2.5L", "agüita", "aguita", "user_phrase", 0.95),
    ("Agua Cielo 2.5L", "agua sin gas", "agua sin gas", "user_phrase", 0.95),
    ("Agua Cielo 2.5L", "h2o", "h2o", "user_phrase", 0.90),
    ("Agua Cielo 2.5L", "hidratación", "hidratacion", "user_phrase", 0.85),
]

# ---------------------------------------------------------------------------
# Columns that are booleans stored as INTEGER in SQLite
# ---------------------------------------------------------------------------
_BOOL_COLUMNS = {"active", "is_active", "requires_human_review", "resolved"}
_JSON_COLUMNS = {
    "nlp_data",
    "extracted_json",
    "clarification_questions",
    "original_extraction",
    "corrected_extraction",
    "options",
    "context",
}


def _ensure_column(cur: sqlite3.Cursor, table: str, column: str, definition: str) -> None:
    columns = {row["name"] for row in cur.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def _init_db() -> None:
    """Create tables and seed data if they don't exist yet."""
    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    cur = con.cursor()
    cur.executescript(_SCHEMA_SQL)
    _ensure_column(cur, "orders", "nlp_data", "JSON")

    # Seed products by name so existing local databases receive new pilot SKUs.
    for name, cat, price, stock in _SEED_PRODUCTS:
        cur.execute("SELECT COUNT(*) FROM products WHERE name = ?", (name,))
        if cur.fetchone()[0] == 0:
            cur.execute(
                "INSERT INTO products (id, name, category, price, stock, active) VALUES (?, ?, ?, ?, ?, 1)",
                (str(uuid.uuid4()), name, cat, price, stock),
            )

    # Seed aliases after products exist.
    for product_name, alias_text, normalized_alias, alias_type, confidence_weight in _SEED_ALIASES:
        product = cur.execute("SELECT id FROM products WHERE name = ? LIMIT 1", (product_name,)).fetchone()
        if not product:
            continue
        cur.execute(
            "SELECT COUNT(*) FROM product_aliases WHERE product_id = ? AND normalized_alias = ?",
            (product["id"], normalized_alias),
        )
        if cur.fetchone()[0] == 0:
            cur.execute(
                """
                INSERT INTO product_aliases
                    (id, product_id, alias_text, normalized_alias, alias_type, confidence_weight, is_active)
                VALUES (?, ?, ?, ?, ?, ?, 1)
                """,
                (str(uuid.uuid4()), product["id"], alias_text, normalized_alias, alias_type, confidence_weight),
            )

    cur.execute(
        """
        UPDATE product_aliases
        SET is_active = 0
        WHERE normalized_alias = 'caja de volt'
          AND product_id IN (SELECT id FROM products WHERE name = 'Volt 500ml')
        """
    )
    cur.execute(
        """
        UPDATE product_aliases
        SET confidence_weight = 1.00
        WHERE normalized_alias = 'big super grande'
          AND product_id IN (SELECT id FROM products WHERE name = 'Big Cola 3L')
        """
    )

    # Seed admin user (only if not exists)
    cur.execute("SELECT COUNT(*) FROM users WHERE email = ?", ("admin@aje.com",))
    if cur.fetchone()[0] == 0:
        cur.execute(
            "INSERT INTO users (id, name, email, phone, password_hash, role) VALUES (?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), "AJE Admin", "admin@aje.com", "77700000", _ADMIN_HASH, "admin"),
        )

    con.commit()
    con.close()


# Run on module import
_init_db()


# ====================================================================
# Response wrapper (mimics postgrest APIResponse)
# ====================================================================

class _Response:
    """Mimics the Supabase execute() response with a .data attribute."""

    def __init__(self, data: List[Dict[str, Any]]):
        self.data = data


# ====================================================================
# Query builder
# ====================================================================

class _QueryBuilder:
    """
    Chainable query builder that mimics:
        db.table("x").select("*").eq("a","b").order("c", desc=True).limit(10).execute()
    """

    def __init__(self, table: str):
        self._table = table
        self._operation: Optional[str] = None          # select | insert | update | delete
        self._select_cols: str = "*"
        self._insert_data: Union[Dict, List[Dict], None] = None
        self._update_data: Optional[Dict] = None
        self._filters: List[tuple] = []                 # [(col, val), ...]
        self._orders: List[tuple] = []                  # [(col, desc_bool), ...]
        self._limit: Optional[int] = None
        # relation joins parsed from select: list of (fk_table, fk_cols)
        self._joins: List[tuple] = []

    # ---------- operation starters ----------

    def select(self, columns: str = "*") -> "_QueryBuilder":
        self._operation = "select"
        self._select_cols = columns
        # Parse relation selectors like "*, products(name)"
        self._joins = []
        relation_re = re.compile(r"(\w+)\(([^)]+)\)")
        for m in relation_re.finditer(columns):
            rel_table = m.group(1)
            rel_cols = [c.strip() for c in m.group(2).split(",")]
            self._joins.append((rel_table, rel_cols))
        return self

    def insert(self, data: Union[Dict, List[Dict]]) -> "_QueryBuilder":
        self._operation = "insert"
        self._insert_data = data
        return self

    def update(self, data: Dict) -> "_QueryBuilder":
        self._operation = "update"
        self._update_data = data
        return self

    def delete(self) -> "_QueryBuilder":
        self._operation = "delete"
        return self

    # ---------- modifiers ----------

    def eq(self, column: str, value: Any) -> "_QueryBuilder":
        self._filters.append((column, value))
        return self

    def order(self, column: str, *, desc: bool = False) -> "_QueryBuilder":
        self._orders.append((column, desc))
        return self

    def limit(self, n: int) -> "_QueryBuilder":
        self._limit = n
        return self

    # ---------- execute ----------

    def execute(self) -> _Response:
        con = sqlite3.connect(str(DB_PATH))
        con.execute("PRAGMA foreign_keys=ON")
        con.row_factory = sqlite3.Row
        try:
            if self._operation == "select":
                return self._exec_select(con)
            elif self._operation == "insert":
                return self._exec_insert(con)
            elif self._operation == "update":
                return self._exec_update(con)
            elif self._operation == "delete":
                return self._exec_delete(con)
            else:
                return _Response([])
        finally:
            con.close()

    # ---------- private helpers ----------

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
        d = dict(row)
        # Convert SQLite booleans back to Python bools for known columns
        for col in _BOOL_COLUMNS:
            if col in d:
                d[col] = bool(d[col])
        for col in _JSON_COLUMNS:
            if isinstance(d.get(col), str):
                try:
                    d[col] = json.loads(d[col])
                except json.JSONDecodeError:
                    pass
        return d

    def _where_clause(self) -> tuple:
        """Build WHERE clause and params from accumulated .eq() calls."""
        if not self._filters:
            return "", []
        parts = []
        params = []
        for col, val in self._filters:
            parts.append(f"{col} = ?")
            # Convert Python bool to int for SQLite
            if isinstance(val, bool):
                params.append(int(val))
            else:
                params.append(val)
        return " WHERE " + " AND ".join(parts), params

    def _order_clause(self) -> str:
        if not self._orders:
            return ""
        parts = []
        for col, desc in self._orders:
            parts.append(f"{col} {'DESC' if desc else 'ASC'}")
        return " ORDER BY " + ", ".join(parts)

    def _limit_clause(self) -> str:
        if self._limit is None:
            return ""
        return f" LIMIT {self._limit}"

    def _resolve_columns(self) -> str:
        """Return the SQL column list for the main table (ignoring relations)."""
        raw = self._select_cols
        # Remove relation selectors
        raw = re.sub(r"\w+\([^)]+\)", "", raw)
        raw = raw.strip().strip(",").strip()
        if not raw or raw == "*":
            return "*"
        # e.g. "stock, name" -> "stock, name"
        return raw

    def _exec_select(self, con: sqlite3.Connection) -> _Response:
        cols = self._resolve_columns()
        where, params = self._where_clause()
        sql = f"SELECT {cols} FROM {self._table}{where}{self._order_clause()}{self._limit_clause()}"
        rows = con.execute(sql, params).fetchall()
        results = [self._row_to_dict(r) for r in rows]

        # Handle relation joins (e.g. products(name))
        if self._joins:
            for row_dict in results:
                for rel_table, rel_cols in self._joins:
                    # Guess the FK column: singular(rel_table) + "_id"
                    fk_col = rel_table.rstrip("s") + "_id"
                    fk_val = row_dict.get(fk_col)
                    if fk_val is not None:
                        rel_sql = f"SELECT {', '.join(rel_cols)} FROM {rel_table} WHERE id = ?"
                        rel_row = con.execute(rel_sql, (fk_val,)).fetchone()
                        if rel_row:
                            row_dict[rel_table] = dict(rel_row)
                        else:
                            row_dict[rel_table] = None
                    else:
                        row_dict[rel_table] = None
        return _Response(results)

    def _exec_insert(self, con: sqlite3.Connection) -> _Response:
        rows_to_insert = self._insert_data if isinstance(self._insert_data, list) else [self._insert_data]
        
        # Check actual table columns to avoid inserting non-existent columns
        pragma_rows = con.execute(f"PRAGMA table_info({self._table})").fetchall()
        table_cols = {r["name"] for r in pragma_rows}

        inserted = []
        for row_data in rows_to_insert:
            row_data = dict(row_data)
            # Auto-generate id and created_at if missing and supported
            if "id" in table_cols and "id" not in row_data:
                row_data["id"] = str(uuid.uuid4())
            if "created_at" in table_cols and "created_at" not in row_data:
                row_data["created_at"] = datetime.now(timezone.utc).isoformat()

            # Convert bools to ints for SQLite
            cleaned = {}
            for k, v in row_data.items():
                if isinstance(v, bool):
                    cleaned[k] = int(v)
                elif isinstance(v, (dict, list)):
                    cleaned[k] = json.dumps(v, ensure_ascii=False)
                else:
                    cleaned[k] = v

            columns = ", ".join(cleaned.keys())
            placeholders = ", ".join("?" for _ in cleaned)
            sql = f"INSERT INTO {self._table} ({columns}) VALUES ({placeholders})"
            con.execute(sql, list(cleaned.values()))
            con.commit()

            # Re-read the inserted row to return consistent data
            result_row = con.execute(
                f"SELECT * FROM {self._table} WHERE id = ?", (row_data["id"],)
            ).fetchone()
            if result_row:
                inserted.append(self._row_to_dict(result_row))

        return _Response(inserted)

    def _exec_update(self, con: sqlite3.Connection) -> _Response:
        if not self._update_data:
            return _Response([])

        # Convert bools
        cleaned = {}
        for k, v in self._update_data.items():
            if isinstance(v, bool):
                cleaned[k] = int(v)
            elif isinstance(v, (dict, list)):
                cleaned[k] = json.dumps(v, ensure_ascii=False)
            else:
                cleaned[k] = v

        set_parts = [f"{k} = ?" for k in cleaned]
        set_params = list(cleaned.values())
        where, where_params = self._where_clause()
        sql = f"UPDATE {self._table} SET {', '.join(set_parts)}{where}"
        con.execute(sql, set_params + where_params)
        con.commit()

        # Return updated rows
        select_sql = f"SELECT * FROM {self._table}{where}"
        rows = con.execute(select_sql, where_params).fetchall()
        return _Response([self._row_to_dict(r) for r in rows])

    def _exec_delete(self, con: sqlite3.Connection) -> _Response:
        where, params = self._where_clause()
        # Fetch rows first so we can return them
        select_sql = f"SELECT * FROM {self._table}{where}"
        rows = con.execute(select_sql, params).fetchall()
        deleted = [self._row_to_dict(r) for r in rows]

        sql = f"DELETE FROM {self._table}{where}"
        con.execute(sql, params)
        con.commit()
        return _Response(deleted)


# ====================================================================
# Client – the object returned by get_supabase() / get_supabase_admin()
# ====================================================================

class LocalSQLiteClient:
    """Drop-in replacement for supabase.Client backed by a local SQLite file."""

    def table(self, name: str) -> _QueryBuilder:
        return _QueryBuilder(name)

    # In case any code checks the URL
    @property
    def supabase_url(self) -> str:
        return "http://localhost:0"

    @property
    def supabase_key(self) -> str:
        return "local-sqlite-key"


# Singleton instance
_client = LocalSQLiteClient()


def get_local_client() -> LocalSQLiteClient:
    """Return the singleton local SQLite client."""
    return _client
