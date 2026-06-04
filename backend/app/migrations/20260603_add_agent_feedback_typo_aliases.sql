-- Agent feedback and typo-tolerant catalogue aliases.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

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

CREATE INDEX IF NOT EXISTS idx_agent_feedback_message ON agent_feedback(message_id);
CREATE INDEX IF NOT EXISTS idx_agent_feedback_user ON agent_feedback(user_id);

WITH alias_seed(product_name, alias_text, normalized_alias, alias_type, confidence_weight) AS (
    VALUES
        ('Big Cola 2L', 'bigg familiar', 'bigg familiar', 'typo_alias', 0.94),
        ('Big Cola 2L', 'bik familiar', 'bik familiar', 'typo_alias', 0.88),
        ('Big Cola 2L', 'big cola dos litrso', 'big cola dos litrso', 'typo_alias', 0.94),
        ('Big Cola 2L', 'bigg cola 2 litros', 'bigg cola 2l', 'typo_alias', 0.94),
        ('Agua Cielo 500ml', 'cielo chika', 'cielo chika', 'typo_alias', 0.96),
        ('Agua Cielo 500ml', 'sielo chica', 'sielo chica', 'typo_alias', 0.92),
        ('Agua Cielo 500ml', 'cieelo chica', 'cieelo chica', 'typo_alias', 0.92),
        ('Volt 300ml', 'votl lata', 'votl lata', 'typo_alias', 0.92),
        ('Volt 300ml', 'vol lata', 'vol lata', 'typo_alias', 0.88),
        ('Volt 300ml', 'bolt lata', 'bolt lata', 'typo_alias', 0.86),
        ('Pulp 300ml', 'pulp chiko', 'pulp chiko', 'typo_alias', 0.92),
        ('Pulp 300ml', 'pulpp chico', 'pulpp chico', 'typo_alias', 0.90),
        ('Cifrut 500ml', 'cifrut chiko', 'cifrut chiko', 'typo_alias', 0.92),
        ('Cifrut 500ml', 'cifru chico', 'cifru chico', 'typo_alias', 0.90),
        ('Cifrut 500ml', 'cifruth chico', 'cifruth chico', 'typo_alias', 0.88),
        ('Oro 2L', 'oro grnade', 'oro grnade', 'typo_alias', 0.90),
        ('Oro 2L', 'oro grand', 'oro grand', 'typo_alias', 0.88)
)
INSERT INTO product_aliases (product_id, alias_text, normalized_alias, alias_type, confidence_weight)
SELECT p.id, a.alias_text, a.normalized_alias, a.alias_type, a.confidence_weight
FROM alias_seed a
JOIN products p ON p.name = a.product_name
ON CONFLICT (product_id, normalized_alias) DO NOTHING;

GRANT ALL ON public.agent_feedback TO service_role;
GRANT ALL ON public.agent_feedback TO authenticated;

ALTER TABLE public.agent_feedback DISABLE ROW LEVEL SECURITY;
