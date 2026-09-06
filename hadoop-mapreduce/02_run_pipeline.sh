#!/usr/bin/env bash
# Sube los inputs a GCS y corre los 3 programas MapReduce en el cluster
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

[ -f work/descriptions.txt ] || python3 01_prepare_inputs.py

CLUSTER=$(terraform -chdir=../terraform output -raw cluster_name)
REGION=$(terraform -chdir=../terraform output -raw region)
ZONE=$(terraform -chdir=../terraform output -raw zone)
BUCKET=$(terraform -chdir=../terraform output -raw bucket_name)
JAR=file:///usr/lib/hadoop-mapreduce/hadoop-mapreduce-examples.jar
echo "Cluster: $CLUSTER | Region: $REGION | Bucket: gs://$BUCKET"

ssh_cmd() {
  gcloud compute ssh "${CLUSTER}-m" --zone "$ZONE" --tunnel-through-iap --command="$1"
}

echo "--- 1. Subiendo inputs a GCS ---"
gcloud storage cp work/descriptions.txt work/customer_quantity.txt "gs://$BUCKET/input/"

echo "--- 2. Copiando inputs de GCS a HDFS ---"
ssh_cmd "
hadoop fs -mkdir -p /retail
hadoop fs -cp -f gs://$BUCKET/input/descriptions.txt /retail/descriptions.txt
hadoop fs -cp -f gs://$BUCKET/input/customer_quantity.txt /retail/customer_quantity.txt
hadoop fs -rm -r -f /retail/wordmean /retail/wordmedian /retail/secondarysort
"

for job in wordmean wordmedian secondarysort; do
  input=/retail/descriptions.txt
  [ "$job" = secondarysort ] && input=/retail/customer_quantity.txt

  echo "--- 3. [$job] enviando job a Dataproc ---"
  gcloud dataproc jobs submit hadoop \
    --cluster="$CLUSTER" --region="$REGION" \
    --jar="$JAR" \
    -- "$job" "$input" "/retail/$job"

  echo "--- 3. [$job] juntando particiones y subiendo resultado a GCS ---"
  ssh_cmd "
  hadoop fs -getmerge /retail/$job /tmp/$job.txt
  gsutil cp /tmp/$job.txt gs://$BUCKET/output/$job.txt
  "
done
