# Deployment and recovery
## Local verification
Run `python -m unittest discover -s tests -v` then `python twin.py`.

## Kafka
Create the shipment-events topic. Publish JSON matching the four fields in streaming.py, keyed by shipment_id. Configure broker authentication through your platform secret manager; the sample assumes a trusted development broker. Never commit secrets.

## Databricks
Install Kafka connector matching the runtime. Set KAFKA_BOOTSTRAP_SERVERS and TWIN_STORAGE_ROOT to a durable cloud storage prefix. Run streaming.py as a job. Bronze persists Kafka coordinates and payloads; malformed records go to quarantine. Monitor quarantine size, source lag, failed jobs and duplicate-ID conflicts. Serialize materialization jobs to avoid concurrent overwrites.

The current implementation deliberately rebuilds silver from retained bronze. This costs a full scan but corrects events arriving beyond any bounded watermark. For large volumes, replace it with changed-shipment MERGE processing and retain the same replay semantics.

## Context and gold publication
The local model accepts weather severity (0–1), port queue hours and supplier due dates. Production enrichment must select context as of the scoring timestamp, validate units, enforce freshness and quarantine missing context. Do not silently substitute calm weather for unavailable observations.
Run assess for each shipment and write its result with port_id and snapshot_at to SHIPMENT_RISK using a Snowflake connector. This publication and external context ingestion are integration steps, not implemented live feeds.

## Airflow
Install the Databricks provider, configure databricks_default using a secret backend, and set twin_databricks_job_id. Deploy supply_chain_dag.py to the DAG folder. Configure the job to run streaming.py. Snowflake publication can be added as a dependent task once context ingestion is configured.

## Recovery
Keep checkpoints durable. Restart failed ingestion using the existing checkpoint. Never delete checkpoints casually: replay into a separate bronze location and validate counts before switching. Duplicate exact events are safe; conflicting IDs block silver publication. Resolve conflicts upstream and replay. Retain bronze long enough to meet your correction SLA.

## Limits
Synthetic demo; heuristic scoring; no live cloud deployment claimed. Full-scan silver, batch timelines and manual gold publication are portfolio-scale starting points. Add schema registry, freshness alerts, authenticated brokers, incremental gold processing and integration tests before production use.
