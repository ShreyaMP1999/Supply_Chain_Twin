"""Run on Databricks with Kafka connector and Delta support."""
import os
from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.getOrCreate()
root = os.environ["TWIN_STORAGE_ROOT"]
schema = "event_id STRING, shipment_id STRING, state STRING, event_time TIMESTAMP"
spark.conf.set("spark.sql.session.timeZone", "UTC")

def ingest():
    raw = (spark.readStream.format("kafka")
           .option("kafka.bootstrap.servers", os.environ["KAFKA_BOOTSTRAP_SERVERS"])
           .option("subscribe", "shipment-events")
           .option("startingOffsets", "earliest").load())
    # Retain original payload and Kafka coordinates for quarantine/replay.
    bronze = raw.selectExpr("CAST(value AS STRING) payload", "topic", "partition", "offset", "timestamp AS ingested_at")
    return (bronze.writeStream.format("delta").outputMode("append")
            .option("checkpointLocation", root + "/checkpoints/bronze")
            .trigger(availableNow=True).start(root + "/bronze"))

def materialize():
    bronze = spark.read.format("delta").load(root + "/bronze")
    parsed = bronze.withColumn("event", F.from_json("payload", schema)).select("*", "event.*")
    valid = (F.col("event_id").isNotNull() & F.col("shipment_id").isNotNull()
             & F.col("event_time").isNotNull()
             & F.col("state").isin("ordered", "departed", "port_arrival", "delivered"))
    parsed.filter(~valid).write.format("delta").mode("overwrite").save(root + "/quarantine")
    clean = parsed.filter(valid).select("event_id", "shipment_id", "state", "event_time").distinct()
    if clean.groupBy("event_id").count().filter("count > 1").limit(1).count():
        raise ValueError("Conflicting event IDs in bronze")
    # Full retained-history rebuild handles arbitrarily late corrections.
    clean.write.format("delta").mode("overwrite").save(root + "/silver")
    timeline = clean.groupBy("shipment_id").agg(
        F.sort_array(F.collect_list(F.struct("event_time", "event_id", "state"))).alias("timeline"))
    timeline.write.format("delta").mode("overwrite").save(root + "/timelines")

if __name__ == "__main__":
    ingest().awaitTermination()
    materialize()
