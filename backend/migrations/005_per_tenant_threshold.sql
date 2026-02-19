-- Phase 3D: Per-Tenant Confidence Threshold
-- Adds confidence_threshold to widget_configs and confidence_threshold to query_logs for observability

ALTER TABLE widget_configs
ADD COLUMN IF NOT EXISTS confidence_threshold FLOAT DEFAULT 0.25;

ALTER TABLE query_logs
ADD COLUMN IF NOT EXISTS confidence_threshold FLOAT;
