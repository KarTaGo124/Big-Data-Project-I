from pathlib import Path

import polars as pl

pl.Config.set_fmt_str_lengths(50)
pl.Config.set_tbl_width_chars(200)

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "online_retail_II.csv"


def print_header(number, title):
    print(f"\n{'=' * 70}")
    print(f"Consulta {number:02d} — {title}")
    print("=" * 70)


def load_raw():
    schema_overrides = {
        "Invoice": pl.Utf8,
        "StockCode": pl.Utf8,
        "Description": pl.Utf8,
        "Customer ID": pl.Float64,
        "Country": pl.Utf8,
    }
    return pl.read_csv(DATA_PATH, schema_overrides=schema_overrides)


def query_01_limpieza(df):
    total_antes = df.height
    limpio = df.filter(pl.col("Description").is_not_null() & (pl.col("Price") > 0))
    total_despues = limpio.height
    print(f"Filas antes: {total_antes}")
    print(f"Filas despues: {total_despues}")
    print(f"Filas eliminadas: {total_antes - total_despues}")
    return limpio


def query_02_duplicados(df):
    total_antes = df.height
    sin_duplicados = df.unique()
    total_despues = sin_duplicados.height
    print(f"Filas antes: {total_antes}")
    print(f"Filas despues: {total_despues}")
    print(f"Duplicados eliminados: {total_antes - total_despues}")
    return sin_duplicados


def query_03_transformacion(df):
    df = df.with_columns(
        pl.col("InvoiceDate").str.to_datetime().alias("InvoiceDate"),
        (pl.col("Quantity") * pl.col("Price")).alias("TotalPrice"),
        pl.col("Invoice").str.starts_with("C").alias("IsCancelled"),
    )
    df = df.with_columns(
        pl.col("InvoiceDate").dt.year().alias("Year"),
        pl.col("InvoiceDate").dt.month().alias("Month"),
    )
    muestra = df.select("Invoice", "TotalPrice", "IsCancelled", "Year", "Month").head(5)
    print(muestra)
    return df


def query_04_filtrado(df):
    total_antes = df.height
    validas = df.filter(
        (pl.col("Quantity") > 0) & (pl.col("Price") > 0) & (~pl.col("IsCancelled"))
    )
    total_despues = validas.height
    print(f"Filas antes: {total_antes}")
    print(f"Ventas validas: {total_despues}")
    return validas


def query_05_top_productos_revenue(df):
    top10 = (
        df.group_by("Description")
        .agg(pl.col("TotalPrice").sum())
        .sort("TotalPrice", descending=True)
        .head(10)
    )
    print(top10)
    return top10


def query_06_top_productos_unidades(df):
    top10 = (
        df.group_by("Description")
        .agg(pl.col("Quantity").sum())
        .sort("Quantity", descending=True)
        .head(10)
    )
    print(top10)
    return top10


def query_07_top_clientes(df):
    top10 = (
        df.filter(pl.col("Customer ID").is_not_null())
        .group_by("Customer ID")
        .agg(pl.col("TotalPrice").sum())
        .sort("TotalPrice", descending=True)
        .head(10)
    )
    print(top10)
    return top10


def query_08_revenue_por_pais(df):
    resumen = (
        df.group_by("Country")
        .agg(
            pl.col("TotalPrice").sum().alias("Revenue"),
            pl.col("Invoice").n_unique().alias("Facturas"),
        )
        .with_columns((pl.col("Revenue") / pl.col("Facturas")).alias("TicketPromedio"))
        .sort("Revenue", descending=True)
        .head(10)
    )
    print(resumen)
    return resumen


def query_09_revenue_mensual(df):
    mensual = (
        df.group_by(["Year", "Month"])
        .agg(pl.col("TotalPrice").sum().alias("Revenue"))
        .sort(["Year", "Month"])
    )
    mensual = mensual.with_columns(
        (pl.col("Revenue").pct_change() * 100).alias("VariacionPct")
    )
    print(mensual)
    return mensual


def query_10_tasa_cancelacion_por_pais(df):
    resumen = (
        df.group_by("Country")
        .agg(
            pl.col("Invoice").count().alias("Total"),
            pl.col("IsCancelled").sum().alias("Canceladas"),
        )
        .filter(pl.col("Total") >= 30)
        .with_columns((pl.col("Canceladas") / pl.col("Total") * 100).alias("TasaCancelacion"))
        .sort("TasaCancelacion", descending=True)
        .head(10)
    )
    print(resumen)
    return resumen


def query_11_segmentacion_clientes(df):
    gasto_por_cliente = (
        df.filter(pl.col("Customer ID").is_not_null())
        .group_by("Customer ID")
        .agg(pl.col("TotalPrice").sum())
    )
    tiers = gasto_por_cliente["TotalPrice"].qcut(3, labels=["Bajo", "Medio", "Alto"])
    conteo = tiers.value_counts()
    orden = {"Bajo": 0, "Medio": 1, "Alto": 2}
    columna = conteo.columns[0]
    conteo = (
        conteo.with_columns(pl.col(columna).cast(pl.Utf8).replace_strict(orden).alias("_orden"))
        .sort("_orden")
        .drop("_orden")
    )
    print(conteo)
    return conteo


def query_12_ticket_promedio(df):
    revenue_total = df["TotalPrice"].sum()
    facturas_totales = df["Invoice"].n_unique()
    aov_global = revenue_total / facturas_totales
    print(f"AOV global: {aov_global:.2f}")

    aov_mensual = (
        df.group_by(["Year", "Month"])
        .agg(
            pl.col("TotalPrice").sum().alias("Revenue"),
            pl.col("Invoice").n_unique().alias("Facturas"),
        )
        .with_columns((pl.col("Revenue") / pl.col("Facturas")).alias("AOV"))
        .sort(["Year", "Month"])
        .select("Year", "Month", "AOV")
    )
    print(aov_mensual)
    return aov_global, aov_mensual


def main():
    df = load_raw()

    print_header(1, "Limpieza de datos")
    df = query_01_limpieza(df)

    print_header(2, "Eliminacion de duplicados")
    df = query_02_duplicados(df)

    print_header(3, "Transformacion de variables")
    df = query_03_transformacion(df)

    print_header(4, "Filtrado de ventas validas")
    ventas_validas = query_04_filtrado(df)

    print_header(5, "Top 10 productos por revenue")
    query_05_top_productos_revenue(ventas_validas)

    print_header(6, "Top 10 productos por unidades vendidas")
    query_06_top_productos_unidades(ventas_validas)

    print_header(7, "Top 10 clientes por gasto total")
    query_07_top_clientes(ventas_validas)

    print_header(8, "Revenue y ticket promedio por pais")
    query_08_revenue_por_pais(ventas_validas)

    print_header(9, "Revenue mensual y variacion")
    query_09_revenue_mensual(ventas_validas)

    print_header(10, "Tasa de cancelacion por pais")
    query_10_tasa_cancelacion_por_pais(df)

    print_header(11, "Segmentacion de clientes por gasto")
    query_11_segmentacion_clientes(ventas_validas)

    print_header(12, "Ticket promedio (AOV) global y mensual")
    query_12_ticket_promedio(ventas_validas)


if __name__ == "__main__":
    main()
