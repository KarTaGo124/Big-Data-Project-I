# Big Data - Proyecto Parcial 2026-2

## Integrantes

- Accilio Villanueva, Ana María
- Cabezas Ramirez, Dylan Andres
- Galvez Pacori, Jose Guillermo
- Meneses Roncal, Matias Alonso
- Salinas Salas, Joaquín Mauricio

## Qué es este proyecto

Proyecto del curso de Big Data: procesar un dataset real de más de un millón de registros aplicando almacenamiento y procesamiento distribuido sobre Google Cloud Platform. El dataset es Online Retail II, transacciones de un minorista de e-commerce del Reino Unido (2009-2011), con problemas de calidad de datos genuinos (nulos, duplicados, precios inválidos, cancelaciones) que se limpian y transforman como parte del pipeline.

Sobre ese dataset se implementó el mismo conjunto de 12 consultas de negocio en cuatro frameworks de procesamiento (Polars, Dask, Modin y Apache Spark), y se ejecutaron tres programas de Hadoop MapReduce sobre un clúster de Google Cloud Dataproc, usando HDFS como sistema de archivos durante el procesamiento. Toda la infraestructura de GCP (bucket y clúster) está definida como código con Terraform.

## Dataset

**Online Retail II** (UCI Machine Learning Repository, DOI 10.24432/C5CG6D), 1,067,371 registros de transacciones de venta. El origen, la estructura de columnas y los hallazgos de calidad de datos están en [`docs/dataset.md`](docs/dataset.md) y en la Sección 2 del informe.

## GCP: almacenamiento y clúster

El dataset se almacena en un bucket de Cloud Storage organizado en tres carpetas (`raw/`, `input/`, `output/`), que además cumple el rol de staging bucket de un clúster de Dataproc (1 master + 2 workers). Toda esta infraestructura se define en Terraform y se levanta o destruye con un solo comando, ver [`terraform/README.md`](terraform/README.md). El diseño completo de la arquitectura está en [`docs/arquitectura.md`](docs/arquitectura.md).

## Procesamiento distribuido

Las 12 consultas (limpieza, deduplicación, transformación, filtrado, agrupaciones y métricas de negocio) están implementadas de forma independiente en `processing/polars/`, `processing/dask/`, `processing/modin/` y `processing/spark/`, cada una con su propio `requirements.txt`. También se corrió un benchmark de tiempo y memoria entre los cuatro frameworks (`processing/run_benchmark.py`). Instrucciones de instalación y ejecución en [`processing/README.md`](processing/README.md).

## Hadoop MapReduce

Sobre el mismo clúster de Dataproc se ejecutaron tres programas de `hadoop-mapreduce-examples.jar` (`wordmean`, `wordmedian`, `secondarysort`) sobre HDFS, usando como entrada archivos de texto derivados del dataset. El detalle operativo, los comandos y los resultados reales están en [`hadoop-mapreduce/README.md`](hadoop-mapreduce/README.md).

## Estructura del repositorio

- `data/`: dataset del proyecto (`online_retail_II.csv`).
- `docs/`: informe técnico en LaTeX/PDF, diseño de arquitectura, ficha del dataset y evidencia de la ejecución real (capturas de GCP, logs de las corridas, benchmarks).
- `notebooks/`: exploración inicial del dataset (calidad de datos, nulos, duplicados, métricas preliminares).
- `processing/`: implementación de las 12 consultas en Polars, Dask, Modin y Spark, más el script de benchmark.
- `hadoop-mapreduce/`: scripts para preparar los inputs, correr los tres programas de Hadoop en Dataproc y descargar los resultados.
- `terraform/`: infraestructura de GCP como código (bucket, clúster Dataproc, apagado automático).

## Cómo reproducir el proyecto

El orden recomendado, de punta a punta:

1. **Infraestructura.** Levantar el bucket y el clúster de Dataproc con Terraform, ver [`terraform/README.md`](terraform/README.md).
2. **Procesamiento distribuido.** Instalar y correr cada framework, local o sobre el clúster, ver [`processing/README.md`](processing/README.md).
3. **Hadoop MapReduce.** Con el clúster ya levantado, correr los tres programas sobre HDFS, ver [`hadoop-mapreduce/README.md`](hadoop-mapreduce/README.md).
4. **Informe y evidencia.** El informe técnico final está en [`docs/informe/main.pdf`](docs/informe/main.pdf) (fuente en `docs/informe/`), y la evidencia de las corridas reales sobre GCP está en [`docs/evidencia/`](docs/evidencia/).
