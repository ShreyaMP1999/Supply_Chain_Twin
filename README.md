# Supply Chain Twin
Global Shipment Disruption Intelligence

Combine shipment events, weather, port congestion and simulated supplier orders to explain delivery risks.

## Run locally
Python 3.10+; no dependencies required:
```sh
python -m unittest discover -s tests -v
python twin.py
```
The demo deliberately receives a delivery event before its departure event, deduplicates retries, reconstructs event-time order, and prints explainable risk scores.

## Architecture
Kafka shipment topic → Databricks bronze Delta → event-time silver reconstruction → risk gold → Snowflake reporting. Airflow orchestrates the daily materialization.
- `twin.py`: executable reference model and deterministic simulated inputs.
- `streaming.py`: Databricks Kafka ingestion and Delta materialization.
- `warehouse.sql`: Snowflake reporting tables and bottleneck views.
- `supply_chain_dag.py`: Airflow orchestration.
- `tests/test_twin.py`: behavioral verification.
- `OPERATIONS.md`: deployment and recovery.

## Semantics
UTC timestamps are mandatory. Event IDs are globally unique. Conflicting duplicate IDs fail validation. Arrival order never determines shipment status. The reference model retains all events, so late historical events can correct a timeline. Streaming bronze is append-only; silver is rebuilt from retained bronze to preserve events beyond a streaming watermark. No shipment is finalized merely because a watermark advanced.

All sample data is synthetic. Risk is a transparent heuristic, not a calibrated delivery prediction. Cloud adapters require infrastructure and have not been executed against live services.
