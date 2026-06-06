-- ============================================================
-- MIGRACIÓN FINAL: Tablas nuevas para el agente LLM
-- Emergentes Preventista — AJE Bolivia
-- Junio 2026
--
-- Compatible con el schema real de Supabase:
-- Todos los IDs son UUID (uuid_generate_v4())
-- Referencias a: users(id), orders(id), stores(id) → todos UUID
-- ============================================================

-- ── 1. Tabla: llm_logs ───────────────────────────────────────
-- Registra cada llamada al LLM con métricas de latencia y tokens.
CREATE TABLE IF NOT EXISTS llm_logs (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id       UUID REFERENCES users(id) ON DELETE SET NULL,
    model         TEXT NOT NULL,
    message       TEXT NOT NULL,
    intent        TEXT,
    raw_response  TEXT,
    parsed_json   JSONB,
    success       BOOLEAN DEFAULT FALSE,
    error         TEXT,
    latency_ms    INTEGER,
    prompt_tokens INTEGER,
    eval_tokens   INTEGER,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- ── 2. Tabla: chat_session_state ──────────────────────────────
-- Estado operativo de la conversación por usuario.
-- Permite resolver respuestas cortas: "de litro", "sí", "mañana".
CREATE TABLE IF NOT EXISTS chat_session_state (
    user_id                UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    active_order_id        UUID REFERENCES orders(id) ON DELETE SET NULL,
    last_detected_products JSONB,
    pending_clarification  JSONB,
    last_store_id          UUID REFERENCES stores(id) ON DELETE SET NULL,
    last_delivery_date     DATE,
    updated_at             TIMESTAMPTZ DEFAULT NOW(),
    expires_at             TIMESTAMPTZ
);

-- ── 3. Nuevas columnas en product_aliases ─────────────────────
-- Permite saber el origen de cada alias (manual, feedback, LLM, etc.)
ALTER TABLE product_aliases
    ADD COLUMN IF NOT EXISTS region     TEXT DEFAULT 'cochabamba_cercado',
    ADD COLUMN IF NOT EXISTS source     TEXT DEFAULT 'manual',
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- ── 4. Índices de rendimiento ─────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_llm_logs_user_created
    ON llm_logs(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_llm_logs_intent
    ON llm_logs(intent);

CREATE INDEX IF NOT EXISTS idx_llm_logs_success
    ON llm_logs(success, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_chat_session_expires
    ON chat_session_state(expires_at)
    WHERE expires_at IS NOT NULL;

-- ── 5. Row Level Security (RLS) ───────────────────────────────
ALTER TABLE llm_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_session_state ENABLE ROW LEVEL SECURITY;

-- Admins pueden ver todos los logs (users.id y auth.uid() son ambos UUID → sin cast)
CREATE POLICY "Admins can read llm_logs" ON llm_logs
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM users
            WHERE users.id = auth.uid()
              AND users.role = 'admin'
        )
    );

-- El backend inserta con service_role key → sin restricción
CREATE POLICY "Service role insert llm_logs" ON llm_logs
    FOR INSERT WITH CHECK (TRUE);

-- Cada usuario gestiona solo su propio estado de sesión
CREATE POLICY "Users own session state" ON chat_session_state
    FOR ALL USING (user_id = auth.uid());

-- ── Verificación ──────────────────────────────────────────────
-- Corre esto aparte para confirmar:
-- SELECT table_name, column_name, data_type
-- FROM information_schema.columns
-- WHERE table_schema = 'public'
--   AND table_name IN ('llm_logs', 'chat_session_state')
-- ORDER BY table_name, ordinal_position;

-- ── 6. Permisos de Roles y RLS ────────────────────────────────
-- Permisos completos para service_role y authenticated
GRANT ALL ON public.llm_logs TO service_role;
GRANT ALL ON public.chat_session_state TO service_role;
GRANT ALL ON public.llm_logs TO authenticated;
GRANT ALL ON public.chat_session_state TO authenticated;

-- El backend maneja su propia auth, por lo que deshabilitamos RLS
-- (igual que en grant_permissions.sql del proyecto)
ALTER TABLE public.llm_logs DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_session_state DISABLE ROW LEVEL SECURITY;
