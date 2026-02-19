-- Phase 3A: Retrieval Metrics Instrumentation
-- Adds structured retrieval intelligence columns to query_logs

ALTER TABLE query_logs
ADD COLUMN IF NOT EXISTS top_score FLOAT,
ADD COLUMN IF NOT EXISTS avg_score FLOAT,
ADD COLUMN IF NOT EXISTS fallback_triggered BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS retrieval_mode VARCHAR(20),
ADD COLUMN IF NOT EXISTS context_tokens INTEGER;
