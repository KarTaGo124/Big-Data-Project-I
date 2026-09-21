import argparse
import importlib.util
import json
import os
import threading
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent


def load_module(framework):
    path = HERE / framework / "queries.py"
    spec = importlib.util.spec_from_file_location(f"{framework}_queries", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MemorySampler:
    def __init__(self, interval=0.1):
        self.interval = interval
        self.peak_rss = 0
        self._stop = threading.Event()
        self._proc = psutil.Process(os.getpid())
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _sample(self):
        total = 0
        try:
            total += self._proc.memory_info().rss
            for child in self._proc.children(recursive=True):
                try:
                    total += child.memory_info().rss
                except psutil.NoSuchProcess:
                    pass
        except psutil.NoSuchProcess:
            pass
        return total

    def _run(self):
        while not self._stop.is_set():
            self.peak_rss = max(self.peak_rss, self._sample())
            time.sleep(self.interval)

    def start(self):
        self.peak_rss = self._sample()
        self._thread.start()

    def stop(self):
        self._stop.set()
        self._thread.join(timeout=2)
        return self.peak_rss


def run_dask_full(mod, timings):
    start = time.perf_counter()
    df = mod.load_raw()
    timings["load_raw"] = time.perf_counter() - start

    start = time.perf_counter()
    df = mod.query_01_limpieza(df)
    timings["query_01"] = time.perf_counter() - start

    start = time.perf_counter()
    df = mod.query_02_duplicados(df)
    timings["query_02"] = time.perf_counter() - start

    start = time.perf_counter()
    df = mod.query_03_transformacion(df)
    df = df.persist()
    timings["query_03"] = time.perf_counter() - start

    start = time.perf_counter()
    validas = mod.query_04_filtrado(df)
    validas = validas.persist()
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


def run_spark_full(mod, timings):
    from pyspark.sql import SparkSession

    start = time.perf_counter()
    spark = SparkSession.builder.appName("benchmark-online-retail").getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    timings["spark_session_init"] = time.perf_counter() - start

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

    spark.stop()


def run_eager_full(mod, timings):
    start = time.perf_counter()
    df = mod.load_raw()
    timings["load_raw"] = time.perf_counter() - start

    start = time.perf_counter()
    df = mod.query_01_limpieza(df)
    timings["query_01"] = time.perf_counter() - start

    start = time.perf_counter()
    df = mod.query_02_duplicados(df)
    timings["query_02"] = time.perf_counter() - start

    start = time.perf_counter()
    df = mod.query_03_transformacion(df)
    timings["query_03"] = time.perf_counter() - start

    start = time.perf_counter()
    validas = mod.query_04_filtrado(df)
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


RUNNERS = {
    "polars": run_eager_full,
    "modin": run_eager_full,
    "dask": run_dask_full,
    "spark": run_spark_full,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("framework", choices=["polars", "dask", "modin", "spark"])
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    mod = load_module(args.framework)
    timings = {}

    sampler = MemorySampler(interval=0.1)
    sampler.start()
    wall_start = time.perf_counter()

    RUNNERS[args.framework](mod, timings)

    wall_total = time.perf_counter() - wall_start
    peak_rss = sampler.stop()

    result = {
        "framework": args.framework,
        "wall_total_seconds": wall_total,
        "peak_memory_mb": peak_rss / (1024 * 1024),
        "stage_timings_seconds": timings,
    }

    Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
