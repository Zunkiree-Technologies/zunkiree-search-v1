-- Phase 4A: Adaptive Retrieval Layer
-- Add rerank_triggered flag to query_logs for observability

ALTER TABLE query_logs
ADD COLUMN IF NOT EXISTS rerank_triggered BOOLEAN DEFAULT FALSE;
