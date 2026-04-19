-- New schema changes for customer_metrics table
-- Target: acme_nexus_analytics.ANALYTICS.METRICS.customer_metrics

-- Destructive: drop deprecated column
ALTER TABLE customer_metrics DROP COLUMN legacy_score;

-- Destructive: rename for clarity
ALTER TABLE customer_metrics RENAME COLUMN avg_order TO avg_order_value;

-- Destructive: widen type for precision
ALTER TABLE customer_metrics ALTER COLUMN total_amount TYPE NUMERIC(18,4);

-- Additive: new loyalty tier column
ALTER TABLE customer_metrics ADD COLUMN loyalty_tier VARCHAR(20);
