-- ============================================================
-- Preventista Inteligente AJE — Database Schema
-- Run this SQL in the Supabase SQL Editor
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─── Users ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        TEXT NOT NULL,
    email       TEXT UNIQUE NOT NULL,
    phone       TEXT NOT NULL DEFAULT '',
    password_hash TEXT NOT NULL,
    role        TEXT NOT NULL DEFAULT 'client',  -- 'client' | 'admin'
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- ─── Stores ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS stores (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    address     TEXT NOT NULL DEFAULT '',
    latitude    DECIMAL NOT NULL DEFAULT 0,
    longitude   DECIMAL NOT NULL DEFAULT 0,
    phone       TEXT DEFAULT '',
    notes       TEXT DEFAULT '',
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- ─── Products ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS products (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        TEXT NOT NULL,
    category    TEXT NOT NULL DEFAULT 'General',
    price       DECIMAL NOT NULL DEFAULT 0,
    stock       INTEGER NOT NULL DEFAULT 0,
    active      BOOLEAN NOT NULL DEFAULT true,
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- ─── Product Aliases ─────────────────────────────────────────
-- The current MVP treats each row in products as a sellable SKU
-- (for example "Big Cola 2L"). Aliases point natural phrases to
-- those SKU rows without breaking the existing order flow.
CREATE TABLE IF NOT EXISTS product_aliases (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id        UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    alias_text        VARCHAR(150) NOT NULL,
    normalized_alias  VARCHAR(150) NOT NULL,
    alias_type        VARCHAR(50) DEFAULT 'user_phrase',
    confidence_weight DECIMAL(5,2) DEFAULT 1.00,
    is_active         BOOLEAN DEFAULT TRUE,
    created_at        TIMESTAMPTZ DEFAULT now(),
    UNIQUE (product_id, normalized_alias)
);

-- ─── Orders ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS orders (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id       UUID REFERENCES users(id) ON DELETE CASCADE,
    store_id      UUID REFERENCES stores(id) ON DELETE SET NULL,
    status        TEXT NOT NULL DEFAULT 'borrador',
    delivery_date DATE,
    total         DECIMAL NOT NULL DEFAULT 0,
    notes         TEXT DEFAULT '',
    nlp_data      JSONB,
    created_at    TIMESTAMPTZ DEFAULT now()
);

-- ─── Order Items ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS order_items (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id    UUID REFERENCES orders(id) ON DELETE CASCADE,
    product_id  UUID REFERENCES products(id) ON DELETE SET NULL,
    quantity    INTEGER NOT NULL DEFAULT 1,
    unit_price  DECIMAL NOT NULL DEFAULT 0,
    subtotal    DECIMAL NOT NULL DEFAULT 0
);

-- ─── Chat Messages ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS chat_messages (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
    order_id    UUID REFERENCES orders(id) ON DELETE CASCADE,
    message     TEXT NOT NULL DEFAULT '',
    sender      TEXT NOT NULL DEFAULT 'user',  -- 'user' | 'system' | 'empresa'
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- ─── Agent Feedback ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS agent_feedback (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
    message_id  UUID NOT NULL REFERENCES chat_messages(id) ON DELETE CASCADE,
    order_id    UUID REFERENCES orders(id) ON DELETE CASCADE,
    rating      VARCHAR(20) NOT NULL CHECK (rating IN ('like', 'dislike')),
    comment     TEXT,
    context     JSONB,
    created_at  TIMESTAMPTZ DEFAULT now(),
    updated_at  TIMESTAMPTZ DEFAULT now(),
    UNIQUE (user_id, message_id)
);

-- ─── Notifications ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS notifications (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
    order_id    UUID REFERENCES orders(id) ON DELETE CASCADE,
    type        TEXT NOT NULL DEFAULT 'chat',  -- 'chat' | 'email'
    message     TEXT NOT NULL DEFAULT '',
    status      TEXT NOT NULL DEFAULT 'pendiente',  -- 'enviado' | 'pendiente' | 'fallido'
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- ─── NLP Audit Tables ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS nlp_interactions (
    id                    UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id               UUID REFERENCES users(id) ON DELETE SET NULL,
    store_id              UUID REFERENCES stores(id) ON DELETE SET NULL,
    raw_text              TEXT NOT NULL,
    normalized_text       TEXT,
    detected_intent       VARCHAR(80),
    extracted_json        JSONB,
    confidence_score      DECIMAL(5,2),
    validation_status     VARCHAR(50),
    requires_human_review BOOLEAN DEFAULT FALSE,
    clarification_questions JSONB,
    created_at            TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS nlp_corrections (
    id                   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    interaction_id       UUID NOT NULL REFERENCES nlp_interactions(id) ON DELETE CASCADE,
    original_extraction  JSONB NOT NULL,
    corrected_extraction JSONB NOT NULL,
    correction_reason    TEXT,
    corrected_by         UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at           TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS clarification_events (
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    interaction_id UUID REFERENCES nlp_interactions(id) ON DELETE CASCADE,
    user_id        UUID REFERENCES users(id) ON DELETE SET NULL,
    store_id       UUID REFERENCES stores(id) ON DELETE SET NULL,
    question_type  VARCHAR(80) NOT NULL,
    question_text  TEXT NOT NULL,
    options        JSONB,
    answer_text    TEXT,
    resolved       BOOLEAN DEFAULT FALSE,
    created_at     TIMESTAMPTZ DEFAULT now()
);

-- ─── Indexes ─────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_stores_user ON stores(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_chat_order ON chat_messages(order_id);
CREATE INDEX IF NOT EXISTS idx_agent_feedback_message ON agent_feedback(message_id);
CREATE INDEX IF NOT EXISTS idx_agent_feedback_user ON agent_feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_product_aliases_normalized ON product_aliases(normalized_alias) WHERE is_active;
CREATE INDEX IF NOT EXISTS idx_product_aliases_product ON product_aliases(product_id);
CREATE INDEX IF NOT EXISTS idx_nlp_interactions_user ON nlp_interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_nlp_interactions_status ON nlp_interactions(validation_status);
CREATE INDEX IF NOT EXISTS idx_clarification_events_interaction ON clarification_events(interaction_id);

-- ─── Seed Products (AJE catalogue) ──────────────────────────
INSERT INTO products (name, category, price, stock) VALUES
    ('Big Cola 3L', 'Bebidas', 12.00, 200),
    ('Big Cola 2L', 'Bebidas', 9.00, 300),
    ('Big Cola 1L', 'Bebidas', 6.00, 400),
    ('Big Cola 500ml', 'Bebidas', 4.00, 500),
    ('Coca-Cola 2L', 'Bebidas', 14.00, 150),
    ('Coca-Cola 1L', 'Bebidas', 10.00, 250),
    ('Coca-Cola 500ml', 'Bebidas', 7.00, 350),
    ('Sporade 500ml', 'Hidratantes', 8.00, 300),
    ('Sporade 1L', 'Hidratantes', 12.00, 200),
    ('Cifrut 500ml', 'Jugos', 5.00, 400),
    ('Cifrut 1L', 'Jugos', 8.00, 250),
    ('Cifrut 2L', 'Jugos', 12.00, 150),
    ('Volt 300ml', 'Energizantes', 8.00, 200),
    ('Volt 500ml', 'Energizantes', 12.00, 150),
    ('Agua Cielo 500ml', 'Agua', 3.00, 600),
    ('Agua Cielo 1L', 'Agua', 5.00, 400),
    ('Agua Cielo 2.5L', 'Agua', 8.00, 200),
    ('Pulp 300ml', 'Jugos', 5.00, 300),
    ('Pulp 1L', 'Jugos', 9.00, 200),
    ('Oro 500ml', 'Bebidas', 4.50, 300),
    ('Oro 2L', 'Bebidas', 8.50, 220),
    ('Free Tea 500ml', 'Té', 6.00, 250)
ON CONFLICT DO NOTHING;

-- ─── Seed Product Aliases ───────────────────────────────────
WITH alias_seed(product_name, alias_text, normalized_alias, alias_type, confidence_weight) AS (
    VALUES
        ('Big Cola 500ml', 'big cola 500 ml', 'big cola 500ml', 'official', 1.00),
        ('Big Cola 500ml', 'big chica', 'big chica', 'size_alias', 0.95),
        ('Big Cola 500ml', 'big personal', 'big personal', 'size_alias', 0.95),
        ('Big Cola 500ml', 'big chiquita', 'big chiquita', 'size_alias', 0.92),
        ('Big Cola 1L', 'big cola 1 litro', 'big cola 1l', 'official', 1.00),
        ('Big Cola 1L', 'big litro', 'big litro', 'size_alias', 1.00),
        ('Big Cola 2L', 'big cola 2 litros', 'big cola 2l', 'official', 1.00),
        ('Big Cola 2L', 'big cola 2lt', 'big cola 2l', 'official', 1.00),
        ('Big Cola 2L', 'big dos litros', 'big dos litros', 'user_phrase', 1.00),
        ('Big Cola 2L', 'big de dos', 'big de dos', 'user_phrase', 1.00),
        ('Big Cola 2L', 'big de dos litros', 'big de dos litros', 'user_phrase', 1.00),
        ('Big Cola 2L', 'big grande', 'big grande', 'size_alias', 0.93),
        ('Big Cola 2L', 'big familiar', 'big familiar', 'size_alias', 0.97),
        ('Big Cola 2L', 'bigg familiar', 'bigg familiar', 'typo_alias', 0.94),
        ('Big Cola 2L', 'bik familiar', 'bik familiar', 'typo_alias', 0.88),
        ('Big Cola 2L', 'big cola dos litrso', 'big cola dos litrso', 'typo_alias', 0.94),
        ('Big Cola 2L', 'bigg cola 2 litros', 'bigg cola 2l', 'typo_alias', 0.94),
        ('Big Cola 2L', 'cola familiar', 'cola familiar', 'size_alias', 0.96),
        ('Big Cola 2L', 'cola grande', 'cola grande', 'size_alias', 0.90),
        ('Big Cola 3L', 'big cola 3 litros', 'big cola 3l', 'official', 1.00),
        ('Big Cola 3L', 'big tres litros', 'big tres litros', 'user_phrase', 1.00),
        ('Big Cola 3L', 'big de tres', 'big de tres', 'user_phrase', 1.00),
        ('Big Cola 3L', 'big super grande', 'big super grande', 'size_alias', 1.00),
        ('Agua Cielo 500ml', 'cielo chica', 'cielo chica', 'size_alias', 1.00),
        ('Agua Cielo 500ml', 'cielo chico', 'cielo chico', 'size_alias', 1.00),
        ('Agua Cielo 500ml', 'cielo chika', 'cielo chika', 'typo_alias', 0.96),
        ('Agua Cielo 500ml', 'sielo chica', 'sielo chica', 'typo_alias', 0.92),
        ('Agua Cielo 500ml', 'cieelo chica', 'cieelo chica', 'typo_alias', 0.92),
        ('Agua Cielo 500ml', 'cielito chico', 'cielito chico', 'cochabamba_slang', 0.98),
        ('Agua Cielo 500ml', 'cielito', 'cielito', 'cochabamba_slang', 0.92),
        ('Agua Cielo 500ml', 'cielo personal', 'cielo personal', 'size_alias', 0.98),
        ('Agua Cielo 500ml', 'agua chica', 'agua chica', 'size_alias', 0.95),
        ('Agua Cielo 500ml', 'agua personal', 'agua personal', 'size_alias', 0.95),
        ('Agua Cielo 500ml', 'agua cielo chica', 'agua cielo chica', 'size_alias', 1.00),
        ('Agua Cielo 1L', 'cielo 1 litro', 'cielo 1l', 'official', 1.00),
        ('Agua Cielo 1L', 'cielo litro', 'cielo litro', 'size_alias', 1.00),
        ('Agua Cielo 2.5L', 'cielo grande', 'cielo grande', 'size_alias', 0.95),
        ('Agua Cielo 2.5L', 'agua grande', 'agua grande', 'size_alias', 0.93),
        ('Agua Cielo 2.5L', 'cielo familiar', 'cielo familiar', 'size_alias', 0.92),
        ('Agua Cielo 2.5L', 'agua cielo grande', 'agua cielo grande', 'size_alias', 0.95),
        ('Agua Cielo 2.5L', 'cielo 2.5 litros', 'cielo 2.5l', 'official', 1.00),
        ('Volt 300ml', 'volt lata', 'volt lata', 'unit_alias', 0.95),
        ('Volt 300ml', 'lata de volt', 'lata de volt', 'unit_alias', 0.95),
        ('Volt 300ml', 'votl lata', 'votl lata', 'typo_alias', 0.92),
        ('Volt 300ml', 'vol lata', 'vol lata', 'typo_alias', 0.88),
        ('Volt 300ml', 'bolt lata', 'bolt lata', 'typo_alias', 0.86),
        ('Volt 300ml', 'voltcito', 'voltcito', 'cochabamba_slang', 0.95),
        ('Volt 300ml', 'volt chico', 'volt chico', 'size_alias', 0.95),
        ('Volt 300ml', 'caja de volt', 'caja de volt', 'unit_alias', 0.95),
        ('Volt 300ml', 'cajita de volt', 'cajita de volt', 'unit_alias', 0.95),
        ('Volt 300ml', 'cajas de volt', 'cajas de volt', 'unit_alias', 0.95),
        ('Volt 500ml', 'volt grande', 'volt grande', 'size_alias', 0.92),
        ('Volt 500ml', 'volt medio litro', 'volt medio litro', 'size_alias', 0.92),
        ('Pulp 300ml', 'pulp chico', 'pulp chico', 'size_alias', 0.95),
        ('Pulp 300ml', 'pulp chiquito', 'pulp chiquito', 'size_alias', 0.92),
        ('Pulp 300ml', 'pulp chiko', 'pulp chiko', 'typo_alias', 0.92),
        ('Pulp 300ml', 'pulpp chico', 'pulpp chico', 'typo_alias', 0.90),
        ('Pulp 300ml', 'pulpito', 'pulpito', 'cochabamba_slang', 0.95),
        ('Pulp 300ml', 'pulp mango chico', 'pulp mango chico', 'user_phrase', 0.85),
        ('Pulp 1L', 'pulp litro', 'pulp litro', 'size_alias', 1.00),
        ('Cifrut 500ml', 'cifrut chico', 'cifrut chico', 'size_alias', 0.95),
        ('Cifrut 500ml', 'cifrut chiquito', 'cifrut chiquito', 'size_alias', 0.92),
        ('Cifrut 500ml', 'cifrut chiko', 'cifrut chiko', 'typo_alias', 0.92),
        ('Cifrut 500ml', 'cifru chico', 'cifru chico', 'typo_alias', 0.90),
        ('Cifrut 500ml', 'cifruth chico', 'cifruth chico', 'typo_alias', 0.88),
        ('Cifrut 500ml', 'cifrutcito', 'cifrutcito', 'cochabamba_slang', 0.95),
        ('Cifrut 1L', 'cifrut litro', 'cifrut litro', 'size_alias', 1.00),
        ('Cifrut 1L', 'cifrut de litro', 'cifrut de litro', 'size_alias', 1.00),
        ('Cifrut 2L', 'cifrut grande', 'cifrut grande', 'size_alias', 0.95),
        ('Oro 500ml', 'oro chico', 'oro chico', 'size_alias', 0.95),
        ('Oro 500ml', 'orito', 'orito', 'cochabamba_slang', 0.95),
        ('Oro 2L', 'oro grande', 'oro grande', 'size_alias', 0.95),
        ('Oro 2L', 'oro grnade', 'oro grnade', 'typo_alias', 0.90),
        ('Oro 2L', 'oro grand', 'oro grand', 'typo_alias', 0.88),
        ('Oro 2L', 'oro 2 litros', 'oro 2l', 'official', 1.00)
)
INSERT INTO product_aliases (product_id, alias_text, normalized_alias, alias_type, confidence_weight)
SELECT p.id, a.alias_text, a.normalized_alias, a.alias_type, a.confidence_weight
FROM alias_seed a
JOIN products p ON p.name = a.product_name
ON CONFLICT (product_id, normalized_alias) DO NOTHING;

-- ─── Admin user seed (password: admin123) ────────────────────
-- Hash for 'admin123' generated with bcrypt
INSERT INTO users (name, email, phone, password_hash, role) VALUES
    ('AJE Admin', 'admin@aje.com', '77700000', '$2b$12$CAdtButIc7g4iXP0Fm3pXeTBdWSgR1uox9OintGf6LdNsRycXqxlm', 'admin')
ON CONFLICT (email) DO NOTHING;
