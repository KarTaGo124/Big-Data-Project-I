#!/usr/bin/env bash
# Descarga los resultados finales (ya mergeados por 02_run_pipeline.sh) desde GCS hacia work/ y los muestra en pantalla.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

BUCKET=$(terraform -chdir=../terraform output -raw bucket_name)
gcloud storage cp "gs://$BUCKET/output/*.txt" work/

echo "--- wordmean.txt ---"
cat work/wordmean.txt
echo "--- wordmedian.txt ---"
cat work/wordmedian.txt
echo "--- secondarysort.txt (primeras 10 lineas) ---"
head -10 work/secondarysort.txt
