-- Multi-change test: drop, rename, alter type, and add
ALTER TABLE fact_orders DROP COLUMN created_at;
ALTER TABLE fact_orders RENAME COLUMN customer_id TO user_id;
ALTER TABLE fact_orders ALTER COLUMN amount TYPE DECIMAL(10,2);
ALTER TABLE fact_orders ADD COLUMN processed_at TIMESTAMP;
