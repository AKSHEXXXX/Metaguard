-- Demo schema change for MetaGuard impact analysis
-- Target: acme_nexus_analytics.ANALYTICS.MARTS.fact_orders

ALTER TABLE fact_orders DROP COLUMN legacy_id;
ALTER TABLE fact_orders RENAME COLUMN old_customer_ref TO customer_id;
ALTER TABLE fact_orders ALTER COLUMN amount TYPE VARCHAR(255);
