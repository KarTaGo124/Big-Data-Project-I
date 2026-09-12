# Consultas — Sección 4 (Procesamiento Distribuido)

Mismo set de 12 consultas implementado de forma independiente en Polars, Dask, Modin y Spark. Cada framework lee `data/online_retail_II.csv` desde cero y corre el pipeline completo.

| # | Categoría(s) | Consulta | Qué responde |
|---|---|---|---|
| 1 | Limpieza | Eliminar filas con `Description` nula o `Price <= 0` | ¿Cuántos registros son basura y se descartan? |
| 2 | Duplicados | Detectar y eliminar filas exactamente duplicadas | ¿Cuántas transacciones estaban repetidas? |
| 3 | Transformación de variables | Crear `TotalPrice = Quantity * Price`, parsear `InvoiceDate`, derivar `Year`/`Month`, `IsCancelled` (prefijo `C` en `Invoice`) | Prepara las columnas base para el resto del análisis |
| 4 | Filtrado | Quedarse solo con ventas válidas (`Quantity > 0`, `Price > 0`, no canceladas) | ¿Cuál es el dataset real de ventas efectivas? |
| 5 | Agrupación + Agregación | Top 10 productos por revenue total | ¿Qué productos generan más ingresos? |
| 6 | Agrupación + Agregación | Top 10 productos por unidades vendidas | ¿Qué productos se venden más en volumen? |
| 7 | Agrupación + Ordenamiento | Top 10 clientes por gasto total | ¿Quiénes son los clientes más valiosos? |
| 8 | Agrupación + Ordenamiento | Revenue y ticket promedio por país (top 10) | ¿Qué países aportan más y cómo varía el ticket? |
| 9 | Métrica (serie temporal) | Revenue mensual y variación % mes a mes | ¿Hay estacionalidad o tendencia de crecimiento? |
| 10 | Métrica + Filtrado | Tasa de cancelación por país (top 10, países con volumen mínimo) | ¿Dónde se cancela/devuelve más, proporcionalmente? |
| 11 | Agrupación + Métrica | Segmentar clientes en 3 tiers de gasto (bajo/medio/alto) y contar por tier | ¿Cómo se distribuye la base de clientes por valor? |
| 12 | Métrica | Ticket promedio (AOV) global y su evolución mensual | ¿Crece o decrece el valor promedio de compra? |

Las consultas 1-4 operan sobre el dataset transformado completo (incluye canceladas). La 10 usa ese mismo dataset (necesita ver canceladas vs no canceladas). Las consultas 5-9, 11 y 12 operan sobre el subconjunto filtrado de ventas válidas de la consulta 4.
