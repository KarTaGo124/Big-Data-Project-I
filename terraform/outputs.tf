output "cluster_name" {
  value = google_dataproc_cluster.cluster.name
}

output "region" {
  value = var.region
}

output "bucket_name" {
  value = google_storage_bucket.staging.name
}

output "jupyterlab_url" {
  value       = try(google_dataproc_cluster.cluster.cluster_config[0].endpoint_config[0].http_ports["JupyterLab"], null)
}

output "ssh_command" {
  value = "gcloud compute ssh ${google_dataproc_cluster.cluster.name}-m --zone ${var.zone} --tunnel-through-iap"
}
