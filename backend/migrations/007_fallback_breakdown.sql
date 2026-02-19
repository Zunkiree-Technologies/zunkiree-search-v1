-- Phase 4B.1: Observability Correction
-- Separate fallback causes into distinct fields

ALTER TABLE query_logs
ADD COLUMN IF NOT EXISTS retrieval_blocked BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS llm_declined BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS retrieval_empty BOOLEAN DEFAULT FALSE;
