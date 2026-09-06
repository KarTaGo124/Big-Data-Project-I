# Terraform — Clúster Dataproc (Apache Spark)

Levanta con un solo comando el clúster Dataproc del curso: bucket de staging, clúster `n4-standard-2` (1 master + 2 workers, 100GB `hyperdisk-balanced` cada uno), service account y Cloud Scheduler para auto-apagado diario.

## Qué hace cada archivo

| Archivo | Qué es |
|---|---|
| `main.tf` | La infraestructura en sí: define los 5 recursos que se crean en GCP (bucket, clúster, service account, permiso IAM, job de Cloud Scheduler). Es el archivo que describe el "qué construir". |
| `variables.tf` | Todos los valores configurables (nombre del clúster, región, tipo de máquina, tamaño de disco, horario de auto-apagado, etc.) con su descripción y un valor por defecto razonable. Ninguno tiene datos de una persona en particular — `project_id` es la única sin default, porque cada quien pone el suyo. |
| `terraform.tfvars.example` | Plantilla que copias a `terraform.tfvars` y llenas con tu propio `project_id`. Ese archivo final (`terraform.tfvars`) nunca se sube al repo (está en `.gitignore`), así que tu proyecto personal se queda en tu máquina. |
| `outputs.tf` | Qué información te muestra Terraform al terminar: nombre del clúster, nombre del bucket generado, URL de JupyterLab, y el comando de SSH ya armado y listo para copiar/pegar. |
| `.terraform.lock.hcl` | Fija la versión exacta del provider de Google (v8.1.0) que se probó y validó, para que a todos les instale la misma versión y no haya sorpresas de compatibilidad entre integrantes del grupo. |
| `.gitignore` (en la raíz del repo) | Evita que se suba al repo el estado de Terraform (`.tfstate`, puede contener datos sensibles del proyecto), los binarios del provider (`.terraform/`, pesa >100MB), y `terraform.tfvars` de cada quien. |

## Requisitos previos (una vez por persona/máquina)

```bash
# 1. Instalar terraform (macOS) — Homebrew ya no tiene la fórmula directa
#    por el cambio de licencia de HashiCorp, hay que usar su tap oficial
brew tap hashicorp/tap
brew install hashicorp/tap/terraform

# 2. Tener gcloud CLI instalado y logueado con tu cuenta
gcloud auth login

# 3. Application Default Credentials — esto es lo que usa Terraform para
#    hablar con la API de Google (distinto del login normal del paso 2)
gcloud auth application-default login

# 4. Habilitar las APIs necesarias en TU proyecto (una sola vez)
gcloud services enable dataproc.googleapis.com cloudscheduler.googleapis.com compute.googleapis.com --project TU_PROJECT_ID

# 5. Darle a la service account por defecto de Compute Engine el rol que
#    Dataproc necesita para poder crear los nodos del cluster
gcloud projects add-iam-policy-binding TU_PROJECT_ID \
  --member="serviceAccount:TU_PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/dataproc.worker"
```

`TU_PROJECT_ID` y `TU_PROJECT_NUMBER` los sacas con:
```bash
gcloud projects describe TU_PROJECT_ID --format="value(projectId,projectNumber)"
```

## Cómo levantarlo

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# edita terraform.tfvars y pon tu project_id

terraform init      # descarga los providers (google, random)
terraform plan       # revisa qué se va a crear ANTES de aplicar, no cambia nada todavia
terraform apply      # te pide confirmar con "yes", ahi si crea todo en GCP
```

Al terminar, Terraform imprime los outputs: nombre del bucket generado, nombre del clúster, la URL de JupyterLab (puede tardar 1-2 min extra en estar accesible) y el comando SSH ya armado.

## Cómo entrar al clúster una vez levantado

**Navegador (JupyterLab):** usa la URL del output `jupyterlab_url`, o pídesela a Terraform de nuevo con:
```bash
terraform output jupyterlab_url
```

**Terminal (SSH):** usa el output `ssh_command`, o:
```bash
terraform output ssh_command
```

## Cómo apagarlo / borrarlo

```bash
# Apagar el cluster (sin borrar los discos, mínimo costo mientras no lo usas)
gcloud dataproc clusters stop $(terraform output -raw cluster_name) --region $(terraform output -raw region)

# Borrar TODO lo que creó este Terraform (bucket, cluster, service account, scheduler)
terraform destroy
```

**Importante:** los discos del clúster cuentan contra la cuota `SSD_TOTAL_GB`/Hyperdisk de tu proyecto **aunque el clúster esté detenido** — solo se liberan si lo borras (`terraform destroy` o `gcloud dataproc clusters delete`). Si vas a dejar de usarlo por un buen rato, mejor bórralo y vuelve a correr `terraform apply` cuando lo necesites — total, queda reproducible en segundos.

## Por qué `southamerica-west1` por default

`n4-standard-2` (el tipo de máquina que pide el curso) sufre escasez real de capacidad de Google en varias regiones — no es un error de configuración, es que Google literalmente no tiene esas VMs disponibles en ese momento en esa zona (`ZONE_RESOURCE_POOL_EXHAUSTED`). Se probó sistemáticamente en 32 zonas de LatAm y EE.UU., y `southamerica-west1-a` (Santiago, Chile) fue la primera con capacidad disponible — además es la región de GCP geográficamente más cercana a Perú, así que de paso debería darte mejor latencia.

Esto puede cambiar con el tiempo y varía por proyecto. Si te falla esa región/zona, prueba otra pasando variables:
```bash
terraform apply -var="region=us-west1" -var="zone=us-west1-b"
```
o edítalo directo en tu `terraform.tfvars`.

## Notas sobre cuotas

Cada región tiene su propia cuota de `SSD_TOTAL_GB`/Hyperdisk — normalmente 500GB por región en proyectos de prueba gratuita. Este clúster usa 300GB (100GB × 3 nodos). Si tienes otro clúster corriendo en la misma región con discos SSD/Hyperdisk, podrías toparte con `Insufficient 'SSD_TOTAL_GB' quota` — bórralo primero (no basta con detenerlo) o usa otra región para este.
