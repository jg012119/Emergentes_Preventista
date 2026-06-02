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

-- ─── Orders ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS orders (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id       UUID REFERENCES users(id) ON DELETE CASCADE,
    store_id      UUID REFERENCES stores(id) ON DELETE SET NULL,
    status        TEXT NOT NULL DEFAULT 'borrador',
    delivery_date DATE,
    total         DECIMAL NOT NULL DEFAULT 0,
    notes         TEXT DEFAULT '',
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

-- ─── Indexes ─────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_stores_user ON stores(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_chat_order ON chat_messages(order_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);

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
    ('Free Tea 500ml', 'Té', 6.00, 250)
ON CONFLICT DO NOTHING;

-- ─── Admin user seed (password: admin123) ────────────────────
-- Hash for 'admin123' generated with bcrypt
INSERT INTO users (name, email, phone, password_hash, role) VALUES
    ('AJE Admin', 'admin@aje.com', '77700000', '$2b$12$CAdtButIc7g4iXP0Fm3pXeTBdWSgR1uox9OintGf6LdNsRycXqxlm', 'admin')
ON CONFLICT (email) DO NOTHING;
