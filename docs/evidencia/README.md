# Evidencia — Corrida en Dataproc real

Evidencia de que los 4 frameworks de procesamiento (Sección 4) y los 3 programas de Hadoop MapReduce (Sección 5) corrieron completos en un clúster Dataproc real (1 master + 2 workers), no solo en local. Corrido sobre un proyecto GCP de prueba (ver issue #18) usando el mismo `terraform/main.tf` del repo.

## Bucket (Sección 2)

- `bucket-lista.png` — el bucket `retail-project-<hash>` en la lista general de Cloud Storage del proyecto
- `bucket-raw.png` — carpeta `raw/`: `online_retail_II.csv` (95.9 MB)
- `bucket-input.png` — carpeta `input/`: `descriptions.txt`, `customer_quantity.txt` (inputs de Hadoop)
- `bucket-output.png` — carpeta `output/`: `wordmean.txt`, `wordmedian.txt`, `secondarysort.txt` (resultados de Hadoop)

## Clúster y jobs de Hadoop MapReduce (Sección 5)

- `cluster-running.png` — clúster `dataproc-cluster` en estado "En ejecución"
- `cluster-workers.png` — mismo clúster, confirmando 2 nodos trabajadores
- `dataproc-jobs-completados.png` — los 3 jobs (`wordmean`, `wordmedian`, `secondarysort`) en estado "Completado"
- `hadoop-wordmean.txt` — resultado real: `count 4664518`, `length 24485085` (idéntico a lo documentado en `hadoop-mapreduce/README.md`)
- `hadoop-wordmedian.txt` — tabla de frecuencias real
- (`secondarysort.txt`, ~7MB, no se duplica aquí — ya vive en `hadoop-mapreduce/work/`)

## Procesamiento distribuido — 4 frameworks (Sección 4)

Output completo (12 consultas cada uno) corriendo en el mismo clúster, leyendo el dataset desde el bucket:

- `dask-cluster-output.txt`
- `modin-cluster-output.txt`
- `polars-cluster-output.txt`
- `spark-cluster-output.txt` (confirmado corriendo como aplicación YARN real, no en modo local)

Los 4 dan resultados numéricos idénticos entre sí (mismo AOV, mismos totales de limpieza/filtrado, mismo top 10 de clientes/productos).

## Benchmark de rendimiento local (Sección 4.7 del informe)

- `benchmark/polars-benchmark.json`, `benchmark/dask-benchmark.json`, `benchmark/modin-benchmark.json`, `benchmark/spark-benchmark.json` — salida cruda de `processing/run_benchmark.py` para cada framework: tiempo total, tiempo por consulta y memoria pico (RSS del proceso principal más sus procesos hijos).
- Corrido en la misma máquina, una vez cada framework, en un entorno virtual aislado por framework (mismas versiones que en `processing/<framework>/requirements.txt`), leyendo el mismo `data/online_retail_II.csv` sin caché tibia entre corridas.
- Máquina: Intel Core i7-13620H (10 núcleos / 16 hilos), 16 GB RAM, Windows 11 Pro.
