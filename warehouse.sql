-- Execute in a preselected Snowflake database/schema.
CREATE TABLE IF NOT EXISTS SHIPMENT_RISK (
 shipment_id VARCHAR, port_id VARCHAR, status VARCHAR,
 risk_score FLOAT, delay_hours FLOAT, reasons VARIANT,
 snapshot_at TIMESTAMP_TZ
);
-- Load validated gold snapshots with the Snowflake connector or COPY INTO.
-- Append snapshots; the latest observation per shipment drives reports.
CREATE OR REPLACE VIEW LATEST_SHIPMENT_RISK AS
SELECT * FROM SHIPMENT_RISK
QUALIFY ROW_NUMBER() OVER (
 PARTITION BY shipment_id ORDER BY snapshot_at DESC
) = 1;

CREATE OR REPLACE VIEW PORT_BOTTLENECKS AS
SELECT port_id, COUNT(*) AS active_shipments,
 COUNT_IF(risk_score >= 50) AS high_risk_shipments,
 AVG(delay_hours) AS average_delay_hours
FROM LATEST_SHIPMENT_RISK
WHERE status <> 'delivered'
GROUP BY port_id;
