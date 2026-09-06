# Hadoop MapReduce en Google Cloud Dataproc

Ejecuta 3 programas del `hadoop-mapreduce-examples.jar` sobre el dataset de retail, todo desde el CLI — sin entrar manualmente al clúster (ni navegador, ni SSH interactivo escribiendo comando por comando).

Esto son **scripts, no Terraform**: Terraform (`../terraform/`) solo administra infraestructura (crear/borrar el clúster y los buckets); este pipeline es trabajo a ejecutar *sobre* esa infraestructura ya levantada.

## Estructura

```
hadoop-mapreduce/
  01_prepare_inputs.py     -> extrae columnas del CSV
  02_run_pipeline.sh       -> sube inputs, corre los 3 programas en el cluster
  03_download_results.sh   -> baja los resultados finales
  run_all.sh               -> corre los 3 pasos de un tirón
  work/                    -> todos los archivos (inputs generados + resultados finales)
```

## Los 3 programas elegidos

El enunciado permite cualquier programa de `hadoop-mapreduce-examples.jar` Elegimos estos tres por tener sintaxis simple (`<input> <output>`, sin argumentos ambiguos) y por usar el dataset real:

| Programa | Objetivo | Input | Columna(s) |
|---|---|---|---|
| `wordmean` | Largo promedio de palabra en un texto | `descriptions.txt` | `Description` |
| `wordmedian` | Mediana del largo de palabra en un texto | `descriptions.txt` | `Description` |
| `secondarysort` | Agrupa por una clave y ordena internamente por una segunda (particionamiento/orden secundario en MapReduce) | `customer_quantity.txt` | `Customer ID`, `Quantity` |

`wordmean`/`wordmedian` dan una idea de la consistencia del texto en el catálogo de productos. `secondarysort` agrupa todas las compras de cada cliente y las ordena por cantidad.

## Cómo correrlo

Requisito: el clúster de `../terraform/` ya debe estar `RUNNING`.

### macOS/Linux
```bash
cd hadoop-mapreduce
./run_all.sh
```

### Windows — Git Bash
Los scripts funcionan sin cambios en **Git Bash** (viene incluido en "Git for Windows"). Si no lo tienes:
1. Instala [Git for Windows](https://git-scm.com/download/win) — elige la opción por defecto en cada paso del instalador.
2. Abre **Git Bash** (busca "Git Bash" en el menú de inicio).
3. Verifica que tengas `terraform` y `gcloud` en el PATH — desde Git Bash:
   ```bash
   terraform --version
   gcloud --version
   ```
   Si no salen, agrega a tu `PATH` la carpeta donde instalaste:
   - `terraform.exe` (por defecto: `C:\Program Files\HashiCorp\terraform\` o similar)
   - `gcloud` CLI (por defecto: `C:\Program Files (x86)\Google\Cloud SDK\bin\` o similar)
   
   En Git Bash, agrega esto al final de `~/.bashrc` (crea el archivo si no existe):
   ```bash
   # Agrega terraform y gcloud al PATH si no están
   export PATH="/c/Program Files/HashiCorp/terraform:$PATH"
   export PATH="/c/Program Files (x86)/Google/Cloud SDK/bin:$PATH"
   ```
   Luego cierra y reabre Git Bash.

4. Desde Git Bash, navega y corre:
   ```bash
   cd hadoop-mapreduce
   ./run_all.sh
   ```

O paso a paso:

**1. `01_prepare_inputs.py`** — lee `../data/online_retail_II.csv`, escribe en `work/`:
- `descriptions.txt` — una descripción de producto por línea
- `customer_quantity.txt` — pares `"<CustomerID> <Quantity>"`, uno por línea

**2. `02_run_pipeline.sh`**:
1. Lee `cluster_name`, `region`, `zone` y `bucket_name` directo de los outputs de Terraform.
2. Sube los `.txt` de `work/` a `gs://<bucket>/input/`.
3. Un SSH corto (no interactivo) copia esos inputs de GCS a HDFS.
4. Para cada uno de los 3 programas: se envía el job con `gcloud dataproc jobs submit hadoop` (la forma nativa de correr jobs en Dataproc — no requiere mantener una conexión SSH abierta mientras el job corre), y al terminar, otro SSH corto junta las particiones del resultado (`hadoop fs -getmerge`, el `>` que junta `part-r-00000`, `part-r-00001`, ... en un solo archivo) y lo sube a `gs://<bucket>/output/`.

(La primera versión de este script mandaba todo — los 3 `hadoop jar` y sus merges — en una sola sesión SSH larga. En pruebas reales el túnel SSH vía IAP se cortó a mitad de una corrida larga con `Broken pipe` — el trabajo en el cluster igual terminaba bien, pero el script local reportaba error. `gcloud dataproc jobs submit` no tiene ese problema porque no depende de un túnel persistente: solo hace polling del estado del job vía la API de Dataproc.)

**3. `03_download_results.sh`** — descarga `work/wordmean.txt`, `work/wordmedian.txt`, `work/secondarysort.txt` y los muestra en pantalla.

## Resultados (probado end-to-end, valores reales)

- **`work/wordmean.txt`** — no imprime la media directo, imprime los contadores con los que se calcula:
  ```
  count	4664518
  length	24485085
  ```
  Media = `length / count` ≈ 5.25 caracteres por palabra.

- **`work/wordmedian.txt`** — tabla de frecuencia (largo de palabra → cantidad de palabras de ese largo). La mediana se obtiene acumulando estos conteos ordenados por largo hasta llegar al 50% del total.

- **`work/secondarysort.txt`** — compras agrupadas por `Customer ID`, ordenadas ascendentemente por `Quantity` dentro de cada grupo (~7MB):
  ```
  12348	1
  12348	1
  12348	1
  12348	6
  12348	12
  ...
  ```

