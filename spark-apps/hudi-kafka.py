import os
import sys
import uuid
import json

import pyspark
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType

# Configuration
spark_version = '3.3.1'
SUBMIT_ARGS = f'--packages ' \
              f'org.apache.hudi:hudi-spark3.3-bundle_2.12:0.14.0,' \
              f'org.apache.spark:spark-sql-kafka-0-10_2.12:{spark_version},' \
              f'org.apache.kafka:kafka-clients:2.8.1 ' \
              f'pyspark-shell'
os.environ["PYSPARK_SUBMIT_ARGS"] = SUBMIT_ARGS
os.environ['PYSPARK_PYTHON'] = sys.executable
os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable

# Initialize Spark Session with Hudi extensions and catalog
spark = SparkSession.builder \
    .master("local[*]") \
    .appName("kafka-example") \
    .config('spark.serializer', 'org.apache.spark.serializer.KryoSerializer') \
    .config('spark.sql.extensions', 'org.apache.spark.sql.hudi.HoodieSparkSessionExtension') \
    .config('spark.sql.catalog.spark_catalog', 'org.apache.spark.sql.hudi.catalog.HoodieCatalog') \
    .getOrCreate()

# Set Logging Level for Detailed Logs (Optional)
spark.sparkContext.setLogLevel("WARN")

# Define Hudi options
hudi_options = {
    'hoodie.table.name': 'kafka_data',
    'hoodie.datasource.write.recordkey.field': 'emp_id',
    'hoodie.datasource.write.table.name': 'kafka_data',
    'hoodie.datasource.write.operation': 'upsert',
    'hoodie.datasource.write.precombine.field': 'ts',
    'hoodie.datasource.write.table.type': 'COPY_ON_WRITE',
    'hoodie.upsert.shuffle.parallelism': 2,
    'hoodie.insert.shuffle.parallelism': 2
}

path = "/mnt/hudi-data/hudi_test_table"
BOOT_STRAP = "kafka-container:49094"
TOPIC = "FirstTopic"

# Read Streaming Data from Kafka
kafka_df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", BOOT_STRAP) \
    .option("subscribe", TOPIC) \
    .option("startingOffsets", "latest") \
    .option("includeHeaders", "true") \
    .option("failOnDataLoss", "false") \
    .load()

def process_batch_message(df, batch_id):
    my_df = df.selectExpr("CAST(value AS STRING) as json")
    schema = StructType(
        [
            StructField("emp_id", StringType(), True),
            StructField("employee_name", StringType(), True),
            StructField("department", StringType(), True),
            StructField("state", StringType(), True),
            StructField("salary", IntegerType(), True),
            StructField("age", IntegerType(), True),
            StructField("bonus", IntegerType(), True),
            StructField("ts", TimestampType(), True),
        ]
    )
    clean_df = my_df.select(from_json(col("json").cast("string"), schema).alias("parsed_value")).select("parsed_value.*")
    if clean_df.count() > 0:
        clean_df.write.format("hudi") \
            .options(**hudi_options) \
            .mode("append") \
            .save(path)
    print(f"batch_id: {batch_id}")
    clean_df.show(truncate=False)

query = kafka_df.writeStream \
    .foreachBatch(process_batch_message) \
    .option("checkpointLocation", "/mnt/hudi-data/hudi_test_table/checkpoints") \
    .trigger(processingTime="1 minute") \
    .start()

query.awaitTermination()

