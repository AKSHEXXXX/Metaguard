-- MetaGuard cross-asset blast radius test
-- Targeting acme_nexus_analytics.ANALYTICS.MARTS.fact_orders

-- Destructive: drop region column used for partitioning and dashboard breakdowns
ALTER TABLE fact_orders DROP COLUMN region;
