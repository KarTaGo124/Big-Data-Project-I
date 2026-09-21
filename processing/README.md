# Procesamiento distribuido

Implementación de las 12 consultas de negocio definidas en [`queries_spec.md`](queries_spec.md), una vez por framework: Polars, Dask, Modin y Apache Spark. Las cuatro leen el mismo `data/online_retail_II.csv` y resuelven el mismo conjunto de operaciones (limpieza, deduplicación, transformación, filtrado, agrupaciones, agregaciones y métricas), para poder comparar cómo cada una resuelve exactamente el mismo problema.

## Instalación

Cada framework tiene su propio `requirements.txt` (`processing/<framework>/requirements.txt`), con las versiones exactas usadas en el proyecto. Se recomienda un entorno virtual por framework: Dask, Modin y Spark arrastran versiones de `pandas` que pueden entrar en conflicto entre sí si se instalan en el mismo entorno.

Desde la raíz del repositorio, por ejemplo para Polars:

```bash
python -m venv .venv-polars
source .venv-polars/bin/activate   # Windows: .venv-polars\Scripts\activate
pip install -r processing/polars/requirements.txt
```

Y de la misma forma para `dask`, `modin` y `spark`, cambiando el nombre del entorno y el `requirements.txt` correspondiente.

## Ejecución

Cada implementación se corre como script independiente, desde la raíz del repositorio (las rutas al dataset son relativas al propio `queries.py`, no al directorio desde el que se invoca):

```bash
python processing/polars/queries.py
python processing/dask/queries.py
python processing/modin/queries.py
python processing/spark/queries.py
```

Cada script imprime en pantalla el resultado de las 12 consultas, en el orden descrito en `queries_spec.md`. `processing/spark/queries.py` además respeta la variable de entorno `DATA_PATH` si se quiere apuntar a un CSV distinto al local, por ejemplo `gs://<bucket>/raw/online_retail_II.csv` al correr sobre el clúster de Dataproc.

## Benchmark entre frameworks

`run_benchmark.py` corre el pipeline completo de un solo framework (carga del CSV más las 12 consultas), mide el tiempo de cada etapa con `time.perf_counter` y la memoria RSS pico del proceso con `psutil`, y guarda el resultado en un JSON:

```bash
python processing/run_benchmark.py polars --output resultado-polars.json
python processing/run_benchmark.py spark --output resultado-spark.json
```

El primer argumento es el framework (`polars`, `dask`, `modin` o `spark`) y `--output` es obligatorio. Para que la comparación entre frameworks sea justa, se recomienda correr cada uno por separado, en su propio entorno virtual, sin otros procesos pesados corriendo al mismo tiempo. La salida cruda de la corrida usada en el informe está en `docs/evidencia/benchmark/`.
