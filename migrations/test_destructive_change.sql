-- Testing MetaGuard detection of destructive changes
-- Targeting acme_nexus_analytics.ANALYTICS.MARTS.fact_orders

-- Drop a column with downstream lineage
ALTER TABLE fact_orders DROP COLUMN amount;

-- Rename a column with downstream lineage
ALTER TABLE fact_orders RENAME COLUMN old_customer_ref TO customer_id;
