# Dataset: Online Retail II

## Origen

**Online Retail II** — repositorio UCI Machine Learning Repository (donado en 2019 por Daqing Chen, doi 10.24432/C5CG6D), también disponible como mirror en Kaggle. Contiene transacciones reales de venta de un minorista online del Reino Unido especializado en artículos de regalo únicos, en su mayoría comprados por otros negocios (mayoristas).

Cubre el periodo **01/12/2009 a 09/12/2011** (dos años fiscales completos). El archivo se descarga directamente desde UCI sin necesidad de autenticación, en formato Excel con dos hojas (`Year 2009-2010` y `Year 2010-2011`); en este proyecto se usa la versión combinada en CSV (`data/online_retail_II.csv`).

Se eligió por tener contexto real de negocio (retail / e-commerce), un volumen que supera cómodamente el mínimo pedido, y problemas de calidad de datos genuinos (no es un dataset pre-limpiado), lo que da material real para las tareas de limpieza, deduplicación y transformación que pide el proyecto.

## Estructura

- **Formato:** CSV, tabular, un registro por línea de producto dentro de una factura.
- **Filas:** 1,067,371 registros (supera el mínimo de 500,000 pedido).
- **Columnas:** 8.

## Variables principales

| Variable | Tipo | Descripción |
|---|---|---|
| `Invoice` | texto | Número de factura. Prefijo `C` indica una cancelación/devolución. |
| `StockCode` | texto | Código identificador del producto. |
| `Description` | texto | Nombre/descripción del producto. |
| `Quantity` | entero | Cantidad de unidades. Puede ser negativa (devoluciones). |
| `InvoiceDate` | fecha-hora | Fecha y hora de la transacción. |
| `Price` | decimal | Precio unitario (libras esterlinas, GBP). |
| `Customer ID` | numérico | Identificador del cliente. Puede ser nulo (compras sin registro de cliente). |
| `Country` | texto | País donde se registró la transacción. |

## Hallazgos de la exploración (ver `notebooks/exploracion.ipynb`)

| Hallazgo | Cantidad | % |
|---|---|---|
| Filas totales | 1,067,371 | 100% |
| `Customer ID` nulo | 243,007 | 22.77% |
| `Description` nula | 4,382 | 0.41% |
| Filas duplicadas exactas | 34,335 | 3.22% |
| Facturas canceladas (prefijo `C`) | 19,494 | — |
| `Quantity` negativa | 22,950 | 2.15% |
| `Price` ≤ 0 | 6,207 | 0.58% |
| Países distintos | 43 | — |
| Reino Unido (% del total) | 981,330 | 91.94% |
| Facturas únicas (`Invoice`) | 53,628 | — |
| Clientes únicos (`Customer ID`) | 5,942 | — |
| Productos únicos (`StockCode`) | 5,305 | — |
| Rango temporal | 2009-12-01 → 2011-12-09 | — |

## Métricas de negocio (vista preliminar)

- **Revenue total** (solo transacciones con `Quantity` positiva): **£20,814,291.998**
- **Ticket promedio por factura**: **£359.65**
- Producto más vendido por unidades: `WORLD WAR 2 GLIDERS ASSTD DESIGNS` (108,545 unidades)
- Cliente con mayor gasto acumulado: `18102.0` (£598,215.22)
