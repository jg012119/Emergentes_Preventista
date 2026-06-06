-- ============================================================
-- AJE Bolivia — Preventista App Schema
-- Compatible: Supabase (PostgreSQL) / Local SQLite via local_db.py
-- Last updated: June 2026
-- ============================================================

-- ── Users ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id            TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name          TEXT NOT NULL,
    email         TEXT UNIQUE NOT NULL,
    phone         TEXT NOT NULL DEFAULT '',
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'client',
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- ── Stores ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS stores (
    id         TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id    TEXT REFERENCES users(id) ON DELETE CASCADE,
    name       TEXT NOT NULL,
    address    TEXT NOT NULL DEFAULT '',
    latitude   REAL NOT NULL DEFAULT 0,
    longitude  REAL NOT NULL DEFAULT 0,
    phone      TEXT DEFAULT '',
    notes      TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Products ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS products (
    id         TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name       TEXT NOT NULL,
    category   TEXT NOT NULL DEFAULT 'General',
    price      REAL NOT NULL DEFAULT 0,
    stock      INTEGER NOT NULL DEFAULT 0,
    active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Product Aliases ─────────────────────────────────────────
-- Stores colloquial aliases per product (e.g. "cielito" → Agua Cielo 500ml).
-- Can be edited from the admin panel without code changes.
CREATE TABLE IF NOT EXISTS product_aliases (
    id                TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    product_id        TEXT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    alias_text        TEXT NOT NULL,
    normalized_alias  TEXT NOT NULL,
    alias_type        TEXT DEFAULT 'user_phrase',
    -- Types: official | size_alias | typo_alias | cochabamba_slang | user_phrase | feedback | llm_suggested
    region            TEXT DEFAULT 'cochabamba_cercado',
    source            TEXT DEFAULT 'manual',
    -- Sources: manual | feedback | llm_suggested | imported_dataset
    confidence_weight REAL DEFAULT 1.00,
    is_active         BOOLEAN DEFAULT TRUE,
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    updated_at        TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (product_id, normalized_alias)
);

-- ── Orders ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS orders (
    id            TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id       TEXT REFERENCES users(id) ON DELETE CASCADE,
    store_id      TEXT REFERENCES stores(id) ON DELETE SET NULL,
    status        TEXT NOT NULL DEFAULT 'borrador',
    -- Statuses: borrador | pendiente | confirmado | rechazado | en_proceso | pagado
    delivery_date TEXT,
    total         REAL NOT NULL DEFAULT 0,
    notes         TEXT DEFAULT '',
    nlp_data      JSONB,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- ── Order Items ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS order_items (
    id          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    order_id    TEXT REFERENCES orders(id) ON DELETE CASCADE,
    product_id  TEXT REFERENCES products(id) ON DELETE SET NULL,
    quantity    INTEGER NOT NULL DEFAULT 1,
    unit_price  REAL NOT NULL DEFAULT 0,
    subtotal    REAL NOT NULL DEFAULT 0
);

-- ── Chat Messages ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS chat_messages (
    id         TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id    TEXT REFERENCES users(id) ON DELETE CASCADE,
    order_id   TEXT REFERENCES orders(id) ON DELETE SET NULL,
    message    TEXT NOT NULL DEFAULT '',
    sender     TEXT NOT NULL DEFAULT 'user',
    -- Senders: user | empresa | system | assistant | agent
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Agent Feedback ──────────────────────────────────────────
-- Stores 👍 / 👎 from preventistas for each agent response.
CREATE TABLE IF NOT EXISTS agent_feedback (
    id         TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id    TEXT REFERENCES users(id) ON DELETE CASCADE,
    message_id TEXT NOT NULL REFERENCES chat_messages(id) ON DELETE CASCADE,
    order_id   TEXT REFERENCES orders(id) ON DELETE SET NULL,
    rating     TEXT NOT NULL CHECK (rating IN ('like', 'dislike')),
    comment    TEXT,
    context    JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id, message_id)
);

-- ── Notifications ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS notifications (
    id         TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id    TEXT REFERENCES users(id) ON DELETE CASCADE,
    order_id   TEXT REFERENCES orders(id) ON DELETE SET NULL,
    type       TEXT NOT NULL DEFAULT 'chat',
    message    TEXT NOT NULL DEFAULT '',
    status     TEXT NOT NULL DEFAULT 'pendiente',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── NLP Interactions ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS nlp_interactions (
    id                    TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id               TEXT REFERENCES users(id) ON DELETE SET NULL,
    store_id              TEXT REFERENCES stores(id) ON DELETE SET NULL,
    raw_text              TEXT NOT NULL,
    normalized_text       TEXT,
    detected_intent       TEXT,
    extracted_json        JSONB,
    confidence_score      REAL,
    validation_status     TEXT,
    requires_human_review BOOLEAN DEFAULT FALSE,
    clarification_questions JSONB,
    created_at            TIMESTAMPTZ DEFAULT NOW()
);

-- ── NLP Corrections ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS nlp_corrections (
    id                   TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    interaction_id       TEXT NOT NULL REFERENCES nlp_interactions(id) ON DELETE CASCADE,
    original_extraction  JSONB NOT NULL,
    corrected_extraction JSONB NOT NULL,
    correction_reason    TEXT,
    corrected_by         TEXT REFERENCES users(id) ON DELETE SET NULL,
    created_at           TIMESTAMPTZ DEFAULT NOW()
);

-- ── Clarification Events ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS clarification_events (
    id             TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    interaction_id TEXT REFERENCES nlp_interactions(id) ON DELETE CASCADE,
    user_id        TEXT REFERENCES users(id) ON DELETE SET NULL,
    store_id       TEXT REFERENCES stores(id) ON DELETE SET NULL,
    question_type  TEXT NOT NULL,
    question_text  TEXT NOT NULL,
    options        JSONB,
    answer_text    TEXT,
    resolved       BOOLEAN DEFAULT FALSE,
    created_at     TIMESTAMPTZ DEFAULT NOW()
);

-- ── LLM Logs ─────────────────────────────────────────────────
-- Records every inference call to Ollama for performance tracking and debugging.
-- Fields from Ollama API: prompt_eval_count, eval_count, total_duration_ms.
CREATE TABLE IF NOT EXISTS llm_logs (
    id            TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id       TEXT REFERENCES users(id) ON DELETE SET NULL,
    model         TEXT NOT NULL,
    message       TEXT NOT NULL,
    intent        TEXT,            -- Detected LlamaIntent.intencion
    raw_response  TEXT,            -- Raw Ollama response content
    parsed_json   JSONB,           -- Validated LlamaIntent as JSON
    success       BOOLEAN DEFAULT FALSE,
    error         TEXT,
    latency_ms    INTEGER,         -- Total wall-clock time in ms
    prompt_tokens INTEGER,         -- Ollama: prompt_eval_count
    eval_tokens   INTEGER,         -- Ollama: eval_count
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- ── Chat Session State ────────────────────────────────────────
-- Stores per-user conversational state for multi-turn order conversations.
-- Allows the agent to resolve short replies like "de litro", "sí", "para mañana".
CREATE TABLE IF NOT EXISTS chat_session_state (
    user_id                TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    active_order_id        TEXT REFERENCES orders(id) ON DELETE SET NULL,
    last_detected_products JSONB,       -- Last LlamaProduct[] before confirmation
    pending_clarification  JSONB,       -- {type, question, options, context}
    last_store_id          TEXT REFERENCES stores(id) ON DELETE SET NULL,
    last_delivery_date     TEXT,        -- ISO date string
    updated_at             TIMESTAMPTZ DEFAULT NOW(),
    expires_at             TIMESTAMPTZ  -- Null = no expiry; set to NOW() + 10min in code
);

-- ── Indexes ───────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_orders_user_status     ON orders(user_id, status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at      ON orders(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_messages_user     ON chat_messages(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_feedback_user    ON agent_feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_product_aliases_product ON product_aliases(product_id);
CREATE INDEX IF NOT EXISTS idx_product_aliases_norm   ON product_aliases(normalized_alias);
CREATE INDEX IF NOT EXISTS idx_llm_logs_user          ON llm_logs(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_llm_logs_intent        ON llm_logs(intent);
