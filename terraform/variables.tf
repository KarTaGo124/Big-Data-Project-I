# ---------------------------------------------------------------------------
# Variables sin default: cada persona del grupo DEBE definir la suya propia.
# No pongas esto directo aqui — copia terraform.tfvars.example a
# terraform.tfvars y pon ahi tus valores (ese archivo esta en .gitignore,
# nunca se sube al repo).
# ---------------------------------------------------------------------------
variable "project_id" {
  description = "ID de tu proyecto de GCP"
  type        = string
}

# ---------------------------------------------------------------------------
# Region / zona. southamerica-west1-a quedo como default porque fue la
# primera zona, de un barrido de 32 zonas de LatAm y EE.UU., que tuvo
# capacidad real disponible para n4-standard-2 (ver README). Puede que en tu
# proyecto/momento otra zona funcione mejor — si community-west1 te falla,
# cambia esto.
# ---------------------------------------------------------------------------
variable "region" {
  description = "Region donde viven el bucket y el cluster"
  type        = string
  default     = "southamerica-west1"
}

variable "zone" {
  description = "Zona especifica dentro de la region para el cluster"
  type        = string
  default     = "southamerica-west1-a"
}

# ---------------------------------------------------------------------------
# Nombres de los recursos
# ---------------------------------------------------------------------------
variable "cluster_name" {
  description = "Nombre del cluster Dataproc"
  type        = string
  default     = "dataproc-cluster"
}

variable "bucket_prefix" {
  description = "Prefijo del bucket de staging"
  type        = string
  default     = "dataproc-staging"
}

variable "scheduler_service_account_id" {
  description = "account_id de la service account dedicada que usa Cloud Scheduler para apagar el cluster"
  type        = string
  default     = "dataproc-auto-stopper"
}

# ---------------------------------------------------------------------------
# Hardware del cluster
# ---------------------------------------------------------------------------
variable "machine_type" {
  description = "Tipo de maquina para el master y los workers (debe cumplir minimo 2 vCPU / 8GB RAM segun especificacion del curso)"
  type        = string
  default     = "n4-standard-2"
}

variable "boot_disk_type" {
  description = "Tipo de disco de arranque. Las familias N4/C4 requieren hyperdisk (no soportan pd-balanced/pd-ssd)"
  type        = string
  default     = "hyperdisk-balanced"
}

variable "boot_disk_size_gb" {
  description = "Tamano del disco primario en GB, para master y cada worker"
  type        = number
  default     = 100
}

variable "num_workers" {
  description = "Cantidad de worker nodes (2+ = cluster Standard; 0 = single node)"
  type        = number
  default     = 2
}

variable "image_version" {
  description = "Version de imagen de Dataproc"
  type        = string
  default     = "2.3-debian12"
}

variable "optional_components" {
  description = "Componentes opcionales a instalar en el cluster"
  type        = list(string)
  default     = ["JUPYTER", "ZOOKEEPER", "PIG"]
}

# ---------------------------------------------------------------------------
# Apagado automatico de respaldo (Cloud Scheduler)
# ---------------------------------------------------------------------------
variable "enable_auto_stop_schedule" {
  description = "Si es true, crea un job de Cloud Scheduler que detiene el cluster automaticamente segun el horario definido abajo "
  type        = bool
  default     = true
}

variable "scheduler_location" {
  description = "Region donde vive el job de Cloud Scheduler (puede ser distinta a la del cluster"
  type        = string
  default     = "us-central1"
}

variable "auto_stop_schedule" {
  description = "Horario cron de apagado automatico"
  type        = string
  default     = "0 12 * * *"
}

variable "auto_stop_timezone" {
  description = "Zona horaria del horario de apagado automatico (formato tz database, ej. America/Lima)"
  type        = string
  default     = "America/Lima"
}
