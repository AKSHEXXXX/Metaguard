-- Multi-change migration for MetaGuard impact analysis demo
-- Target: acme_nexus_analytics.ANALYTICS.MARTS.fact_orders

-- Destructive: drop unused legacy column
ALTER TABLE fact_orders DROP COLUMN legacy_id;

-- Destructive: rename column (breaks direct references)
ALTER TABLE fact_orders RENAME COLUMN old_customer_ref TO customer_id;

-- Destructive: incompatible type change
ALTER TABLE fact_orders ALTER COLUMN amount TYPE VARCHAR(255);

-- Additive: safe new column
ALTER TABLE fact_orders ADD COLUMN created_at TIMESTAMP;
