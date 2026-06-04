-- NLP catalogue aliases and audit tables for existing Supabase projects.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

ALTER TABLE orders ADD COLUMN IF NOT EXISTS nlp_data JSONB;

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

CREATE TABLE IF NOT EXISTS nlp_interactions (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id                 UUID REFERENCES users(id) ON DELETE SET NULL,
    store_id                UUID REFERENCES stores(id) ON DELETE SET NULL,
    raw_text                TEXT NOT NULL,
    normalized_text         TEXT,
    detected_intent         VARCHAR(80),
    extracted_json          JSONB,
    confidence_score        DECIMAL(5,2),
    validation_status       VARCHAR(50),
    requires_human_review   BOOLEAN DEFAULT FALSE,
    clarification_questions JSONB,
    created_at              TIMESTAMPTZ DEFAULT now()
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

CREATE INDEX IF NOT EXISTS idx_product_aliases_normalized ON product_aliases(normalized_alias) WHERE is_active;
CREATE INDEX IF NOT EXISTS idx_product_aliases_product ON product_aliases(product_id);
CREATE INDEX IF NOT EXISTS idx_nlp_interactions_user ON nlp_interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_nlp_interactions_status ON nlp_interactions(validation_status);
CREATE INDEX IF NOT EXISTS idx_clarification_events_interaction ON clarification_events(interaction_id);

WITH product_seed(name, category, price, stock) AS (
    VALUES
        ('Oro 500ml', 'Bebidas', 4.50, 300),
        ('Oro 2L', 'Bebidas', 8.50, 220)
)
INSERT INTO products (name, category, price, stock)
SELECT s.name, s.category, s.price, s.stock
FROM product_seed s
WHERE NOT EXISTS (
    SELECT 1 FROM products p WHERE p.name = s.name
);

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
        ('Big Cola 2L', 'cola familiar', 'cola familiar', 'size_alias', 0.96),
        ('Big Cola 2L', 'cola grande', 'cola grande', 'size_alias', 0.90),
        ('Big Cola 3L', 'big cola 3 litros', 'big cola 3l', 'official', 1.00),
        ('Big Cola 3L', 'big tres litros', 'big tres litros', 'user_phrase', 1.00),
        ('Big Cola 3L', 'big de tres', 'big de tres', 'user_phrase', 1.00),
        ('Big Cola 3L', 'big super grande', 'big super grande', 'size_alias', 0.92),
        ('Agua Cielo 500ml', 'cielo chica', 'cielo chica', 'size_alias', 1.00),
        ('Agua Cielo 500ml', 'cielo chico', 'cielo chico', 'size_alias', 1.00),
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
        ('Volt 300ml', 'voltcito', 'voltcito', 'cochabamba_slang', 0.95),
        ('Volt 300ml', 'volt chico', 'volt chico', 'size_alias', 0.95),
        ('Volt 300ml', 'caja de volt', 'caja de volt', 'unit_alias', 0.95),
        ('Volt 300ml', 'cajita de volt', 'cajita de volt', 'unit_alias', 0.95),
        ('Volt 300ml', 'cajas de volt', 'cajas de volt', 'unit_alias', 0.95),
        ('Volt 500ml', 'volt grande', 'volt grande', 'size_alias', 0.92),
        ('Volt 500ml', 'volt medio litro', 'volt medio litro', 'size_alias', 0.92),
        ('Pulp 300ml', 'pulp chico', 'pulp chico', 'size_alias', 0.95),
        ('Pulp 300ml', 'pulp chiquito', 'pulp chiquito', 'size_alias', 0.92),
        ('Pulp 300ml', 'pulpito', 'pulpito', 'cochabamba_slang', 0.95),
        ('Pulp 300ml', 'pulp mango chico', 'pulp mango chico', 'user_phrase', 0.85),
        ('Pulp 1L', 'pulp litro', 'pulp litro', 'size_alias', 1.00),
        ('Cifrut 500ml', 'cifrut chico', 'cifrut chico', 'size_alias', 0.95),
        ('Cifrut 500ml', 'cifrut chiquito', 'cifrut chiquito', 'size_alias', 0.92),
        ('Cifrut 500ml', 'cifrutcito', 'cifrutcito', 'cochabamba_slang', 0.95),
        ('Cifrut 1L', 'cifrut litro', 'cifrut litro', 'size_alias', 1.00),
        ('Cifrut 1L', 'cifrut de litro', 'cifrut de litro', 'size_alias', 1.00),
        ('Cifrut 2L', 'cifrut grande', 'cifrut grande', 'size_alias', 0.95),
        ('Oro 500ml', 'oro chico', 'oro chico', 'size_alias', 0.95),
        ('Oro 500ml', 'orito', 'orito', 'cochabamba_slang', 0.95),
        ('Oro 2L', 'oro grande', 'oro grande', 'size_alias', 0.95),
        ('Oro 2L', 'oro 2 litros', 'oro 2l', 'official', 1.00)
)
INSERT INTO product_aliases (product_id, alias_text, normalized_alias, alias_type, confidence_weight)
SELECT p.id, a.alias_text, a.normalized_alias, a.alias_type, a.confidence_weight
FROM alias_seed a
JOIN products p ON p.name = a.product_name
ON CONFLICT (product_id, normalized_alias) DO NOTHING;

UPDATE product_aliases
SET is_active = FALSE
WHERE normalized_alias = 'caja de volt'
  AND product_id IN (SELECT id FROM products WHERE name = 'Volt 500ml');

GRANT ALL ON public.product_aliases TO service_role;
GRANT ALL ON public.nlp_interactions TO service_role;
GRANT ALL ON public.nlp_corrections TO service_role;
GRANT ALL ON public.clarification_events TO service_role;
GRANT SELECT ON public.product_aliases TO anon;
GRANT ALL ON public.product_aliases TO authenticated;
GRANT ALL ON public.nlp_interactions TO authenticated;
GRANT ALL ON public.nlp_corrections TO authenticated;
GRANT ALL ON public.clarification_events TO authenticated;
