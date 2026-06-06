-- ============================================================
-- GRANT PERMISSIONS — Preventista Inteligente AJE
-- Ejecutar en: Supabase Dashboard → SQL Editor
-- ============================================================

-- Otorgar permisos completos al service_role en todas las tablas
GRANT ALL ON public.users         TO service_role;
GRANT ALL ON public.stores        TO service_role;
GRANT ALL ON public.products      TO service_role;
GRANT ALL ON public.product_aliases TO service_role;
GRANT ALL ON public.orders        TO service_role;
GRANT ALL ON public.order_items   TO service_role;
GRANT ALL ON public.chat_messages TO service_role;
GRANT ALL ON public.agent_feedback TO service_role;
GRANT ALL ON public.notifications TO service_role;
GRANT ALL ON public.nlp_interactions TO service_role;
GRANT ALL ON public.nlp_corrections TO service_role;
GRANT ALL ON public.clarification_events TO service_role;
GRANT ALL ON public.llm_logs TO service_role;
GRANT ALL ON public.chat_session_state TO service_role;

-- Otorgar permisos de lectura al anon role (para endpoints públicos)
GRANT SELECT ON public.products TO anon;
GRANT SELECT ON public.product_aliases TO anon;

-- Otorgar permisos al authenticated role
GRANT ALL ON public.users         TO authenticated;
GRANT ALL ON public.stores        TO authenticated;
GRANT ALL ON public.products      TO authenticated;
GRANT ALL ON public.product_aliases TO authenticated;
GRANT ALL ON public.orders        TO authenticated;
GRANT ALL ON public.order_items   TO authenticated;
GRANT ALL ON public.chat_messages TO authenticated;
GRANT ALL ON public.agent_feedback TO authenticated;
GRANT ALL ON public.notifications TO authenticated;
GRANT ALL ON public.nlp_interactions TO authenticated;
GRANT ALL ON public.nlp_corrections TO authenticated;
GRANT ALL ON public.clarification_events TO authenticated;
GRANT ALL ON public.llm_logs TO authenticated;
GRANT ALL ON public.chat_session_state TO authenticated;

-- Deshabilitar RLS en todas las tablas (el backend maneja su propia auth con JWT)
ALTER TABLE public.users         DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.stores        DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.products      DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.product_aliases DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.orders        DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.order_items   DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_messages DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.agent_feedback DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.nlp_interactions DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.nlp_corrections DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.clarification_events DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.llm_logs DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_session_state DISABLE ROW LEVEL SECURITY;
