-- NLP tuning after expanded Cochabamba/Cercado dataset.
-- Run this after 20260603_add_agent_feedback_typo_aliases.sql.

UPDATE product_aliases
SET confidence_weight = 1.00
WHERE normalized_alias = 'big super grande'
  AND product_id IN (SELECT id FROM products WHERE name = 'Big Cola 3L');
