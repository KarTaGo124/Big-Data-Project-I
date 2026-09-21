import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import queries as mod  # noqa: E402
from pyspark.sql import SparkSession  # noqa: E402

mod.DATA_PATH = "gs://retail-project-f6e06bc9/raw/online_retail_II.csv"


def main():
    timings = {}

    start = time.perf_counter()
    spark = SparkSession.builder.appName("benchmark-cluster-online-retail").getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    timings["spark_session_init"] = time.perf_counter() - start

    wall_start = time.perf_counter()

    start = time.perf_counter()
    df = mod.load_raw(spark)
    timings["load_raw"] = time.perf_counter() - start

    start = time.perf_counter()
    df = mod.query_01_limpieza(df)
    timings["query_01"] = time.perf_counter() - start

    start = time.perf_counter()
    df = mod.query_02_duplicados(df)
    timings["query_02"] = time.perf_counter() - start

    start = time.perf_counter()
    df = mod.query_03_transformacion(df)
    df = df.cache()
    timings["query_03"] = time.perf_counter() - start

    start = time.perf_counter()
    validas = mod.query_04_filtrado(df)
    validas = validas.cache()
    timings["query_04"] = time.perf_counter() - start

    for n, fn, arg in [
        (5, mod.query_05_top_productos_revenue, validas),
        (6, mod.query_06_top_productos_unidades, validas),
        (7, mod.query_07_top_clientes, validas),
        (8, mod.query_08_revenue_por_pais, validas),
        (9, mod.query_09_revenue_mensual, validas),
        (10, mod.query_10_tasa_cancelacion_por_pais, df),
        (11, mod.query_11_segmentacion_clientes, validas),
        (12, mod.query_12_ticket_promedio, validas),
    ]:
        start = time.perf_counter()
        fn(arg)
        timings[f"query_{n:02d}"] = time.perf_counter() - start

    wall_total = time.perf_counter() - wall_start
    spark.stop()

    result = {
        "framework": "spark",
        "location": "dataproc-cluster (YARN, 1 master + 2 workers)",
        "wall_total_seconds": wall_total,
        "stage_timings_seconds": timings,
    }

    Path("/tmp/spark-cluster-benchmark.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
