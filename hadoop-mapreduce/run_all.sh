#!/usr/bin/env bash
# Corre el pipeline completo: prepara inputs, sube y ejecuta en el cluster, descarga resultados
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

python3 01_prepare_inputs.py
./02_run_pipeline.sh
./03_download_results.sh
