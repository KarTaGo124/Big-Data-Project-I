terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.30.0"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.6.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# ---------------------------------------------------------------------------
# Un solo bucket para todo: staging interno de Dataproc (Dataproc crea sus
# propias subcarpetas ahi automaticamente) + el dataset del proyecto bajo
# "raw/" (zona cruda del data lake)
# ---------------------------------------------------------------------------
resource "google_storage_bucket" "main" {
  name                        = "${var.bucket_prefix}-${random_id.bucket_suffix.hex}"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = true
}

resource "google_storage_bucket_object" "raw_dataset" {
  name   = "${var.dataset_raw_prefix}/${basename(var.dataset_local_path)}"
  bucket = google_storage_bucket.main.name
  source = "${path.module}/${var.dataset_local_path}"
}

# ---------------------------------------------------------------------------
# Cluster Dataproc (Apache Spark) — Standard: 1 master + 2 workers
# n4-standard-2 (2 vCPU, 8GB RAM) con disco hyperdisk-balanced de 100GB.
# ---------------------------------------------------------------------------
resource "google_dataproc_cluster" "cluster" {
  name    = var.cluster_name
  region  = var.region
  project = var.project_id

  cluster_config {
    staging_bucket = google_storage_bucket.main.name

    gce_cluster_config {
      zone = var.zone
      service_account_scopes = [
        "https://www.googleapis.com/auth/cloud-platform",
      ]
    }

    master_config {
      num_instances = 1
      machine_type  = var.machine_type
      disk_config {
        boot_disk_type    = var.boot_disk_type
        boot_disk_size_gb = var.boot_disk_size_gb
      }
    }

    worker_config {
      num_instances = var.num_workers
      machine_type  = var.machine_type
      disk_config {
        boot_disk_type    = var.boot_disk_type
        boot_disk_size_gb = var.boot_disk_size_gb
      }
    }

    software_config {
      image_version       = var.image_version
      optional_components = var.optional_components
    }

    endpoint_config {
      enable_http_port_access = true
    }
  }

  # La API de Dataproc siempre agrega automaticamente scopes extra
  # (devstorage.read_write, logging.write, cloud.useraccounts.readonly) al
  # que declaramos arriba, y ese campo es ForceNew en el provider -> sin
  # esto, cada "terraform plan" ve una diferencia eterna contra la config y
  # quiere destruir/recrear el cluster para siempre (problema conocido del
  # provider google_dataproc_cluster, no algo que dependa de este codigo).
  lifecycle {
    ignore_changes = [
      cluster_config[0].gce_cluster_config[0].service_account_scopes,
    ]
  }
}

# ---------------------------------------------------------------------------
# Service account dedicada, solo para que Cloud Scheduler pueda
# iniciar/detener el cluster (rol acotado a Dataproc, nada mas)
# ---------------------------------------------------------------------------
resource "google_service_account" "auto_stopper" {
  account_id   = var.scheduler_service_account_id
  display_name = "Dataproc Auto Stopper (Cloud Scheduler)"
  project      = var.project_id
}

resource "google_project_iam_member" "dataproc_editor" {
  project = var.project_id
  role    = "roles/dataproc.editor"
  member  = "serviceAccount:${google_service_account.auto_stopper.email}"
}

# ---------------------------------------------------------------------------
# Cloud Scheduler: apaga el cluster automaticamente todos los dias a la hora
# configurada, como respaldo de seguridad por si se olvida apagarlo a mano.
# ---------------------------------------------------------------------------
resource "google_cloud_scheduler_job" "auto_stop_cluster" {
  count = var.enable_auto_stop_schedule ? 1 : 0

  name        = "${var.cluster_name}-auto-stop"
  project     = var.project_id
  region      = var.scheduler_location
  description = "Apaga ${var.cluster_name} automaticamente como respaldo de seguridad"
  schedule    = var.auto_stop_schedule
  time_zone   = var.auto_stop_timezone

  http_target {
    http_method = "POST"
    uri         = "https://dataproc.googleapis.com/v1/projects/${var.project_id}/regions/${var.region}/clusters/${var.cluster_name}:stop"
    body        = base64encode("{}")
    headers = {
      "Content-Type" = "application/json"
    }
    oauth_token {
      service_account_email = google_service_account.auto_stopper.email
      scope                 = "https://www.googleapis.com/auth/cloud-platform"
    }
  }

  depends_on = [google_project_iam_member.dataproc_editor]
}
