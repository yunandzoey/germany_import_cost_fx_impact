# scripts/utils.py
from pyspark.sql import DataFrame as SparkDF
from pyspark.sql import functions as F

def with_ingest_meta(df: SparkDF, src: str) -> SparkDF:
    return (df
            .withColumn("ingest_ts", F.current_timestamp())
            .withColumn("source", F.lit(src)))

def write_delta(df: SparkDF, path: str, mode: str = "overwrite", partition_col: str = None):
    if partition_col:
        (df.write.format("delta").mode(mode).partitionBy(partition_col).save(path))
    else:
        (df.write.format("delta").mode(mode).save(path))
