-- Migration: Create alert_annotations table (idempotent)
CREATE TABLE IF NOT EXISTS alert_annotations (
  id SERIAL PRIMARY KEY,
  alert_id VARCHAR(128) NOT NULL,
  disposition VARCHAR(32) NULL,
  event_time TIMESTAMPTZ NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS ix_alert_annotations_alert_id ON alert_annotations (alert_id);
CREATE INDEX IF NOT EXISTS ix_alert_annotations_updated_at ON alert_annotations (updated_at);
