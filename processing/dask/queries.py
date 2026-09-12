from pathlib import Path

import dask.dataframe as dd
import pandas as pd

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "online_retail_II.csv"


def print_header(number, title):
    print(f"\n{'=' * 70}")
    print(f"Consulta {number:02d} — {title}")
    print("=" * 70)


def load_raw():
    dtypes = {
        "Invoice": "string",
        "StockCode": "string",
        "Description": "string",
        "Customer ID": "float64",
        "Country": "string",
    }
    df = dd.read_csv(DATA_PATH, dtype=dtypes, blocksize="16MB")
    print(f"Particiones: {df.npartitions}")
    return df


def query_01_limpieza(df):
    total_antes = len(df)
    limpio = df[~df["Description"].isna() & (df["Price"] > 0)]
    total_despues = len(limpio)
    print(f"Filas antes: {total_antes}")
    print(f"Filas despues: {total_despues}")
    print(f"Filas eliminadas: {total_antes - total_despues}")
    return limpio


def query_02_duplicados(df):
    total_antes = len(df)
    sin_duplicados = df.drop_duplicates()
    total_despues = len(sin_duplicados)
    print(f"Filas antes: {total_antes}")
    print(f"Filas despues: {total_despues}")
    print(f"Duplicados eliminados: {total_antes - total_despues}")
    return sin_duplicados


def query_03_transformacion(df):
    df = df.assign(
        InvoiceDate=dd.to_datetime(df["InvoiceDate"]),
        TotalPrice=df["Quantity"] * df["Price"],
        IsCancelled=df["Invoice"].str.startswith("C"),
    )
    df["Year"] = df["InvoiceDate"].dt.year
    df["Month"] = df["InvoiceDate"].dt.month
    muestra = df[["Invoice", "TotalPrice", "IsCancelled", "Year", "Month"]].head(5)
    print(muestra.to_string(index=False))
    return df


def query_04_filtrado(df):
    total_antes = len(df)
    validas = df[(df["Quantity"] > 0) & (df["Price"] > 0) & (~df["IsCancelled"])]
    total_despues = len(validas)
    print(f"Filas antes: {total_antes}")
    print(f"Ventas validas: {total_despues}")
    return validas


def query_05_top_productos_revenue(df):
    resultado = df.groupby("Description")["TotalPrice"].sum().compute()
    top10 = resultado.nlargest(10)
    print(top10.to_string())
    return top10


def query_06_top_productos_unidades(df):
    resultado = df.groupby("Description")["Quantity"].sum().compute()
    top10 = resultado.nlargest(10)
    print(top10.to_string())
    return top10


def query_07_top_clientes(df):
    con_cliente = df.dropna(subset=["Customer ID"])
    resultado = con_cliente.groupby("Customer ID")["TotalPrice"].sum().compute()
    top10 = resultado.nlargest(10)
    print(top10.to_string())
    return top10


def query_08_revenue_por_pais(df):
    revenue = df.groupby("Country")["TotalPrice"].sum().compute()
    facturas = df.groupby("Country")["Invoice"].nunique().compute()
    resumen = pd.DataFrame({"Revenue": revenue, "Facturas": facturas})
    resumen["TicketPromedio"] = resumen["Revenue"] / resumen["Facturas"]
    top10 = resumen.sort_values("Revenue", ascending=False).head(10)
    print(top10.to_string())
    return top10


def query_09_revenue_mensual(df):
    mensual = df.groupby(["Year", "Month"])["TotalPrice"].sum().compute()
    mensual = mensual.sort_index()
    variacion = mensual.pct_change() * 100
    resumen = pd.DataFrame({"Revenue": mensual, "VariacionPct": variacion})
    print(resumen.to_string())
    return resumen


def query_10_tasa_cancelacion_por_pais(df):
    total_por_pais = df.groupby("Country")["Invoice"].count().compute()
    canceladas_por_pais = df.groupby("Country")["IsCancelled"].sum().compute()
    resumen = pd.DataFrame({"Total": total_por_pais, "Canceladas": canceladas_por_pais})
    resumen = resumen[resumen["Total"] >= 30]
    resumen["TasaCancelacion"] = resumen["Canceladas"] / resumen["Total"] * 100
    top10 = resumen.sort_values("TasaCancelacion", ascending=False).head(10)
    print(top10.to_string())
    return top10


def query_11_segmentacion_clientes(df):
    con_cliente = df.dropna(subset=["Customer ID"])
    gasto_por_cliente = con_cliente.groupby("Customer ID")["TotalPrice"].sum().compute()
    tiers = pd.qcut(gasto_por_cliente, 3, labels=["Bajo", "Medio", "Alto"])
    conteo = tiers.value_counts().sort_index()
    print(conteo.to_string())
    return conteo


def query_12_ticket_promedio(df):
    revenue_total = df["TotalPrice"].sum().compute()
    facturas_totales = df["Invoice"].nunique().compute()
    aov_global = revenue_total / facturas_totales
    print(f"AOV global: {aov_global:.2f}")

    revenue_mensual = df.groupby(["Year", "Month"])["TotalPrice"].sum().compute()
    facturas_mensual = df.groupby(["Year", "Month"])["Invoice"].nunique().compute()
    aov_mensual = (revenue_mensual / facturas_mensual).sort_index()
    print(aov_mensual.to_string())
    return aov_global, aov_mensual


def main():
    df = load_raw()

    print_header(1, "Limpieza de datos")
    df = query_01_limpieza(df)

    print_header(2, "Eliminacion de duplicados")
    df = query_02_duplicados(df)

    print_header(3, "Transformacion de variables")
    df = query_03_transformacion(df)
    df = df.persist()

    print_header(4, "Filtrado de ventas validas")
    ventas_validas = query_04_filtrado(df)
    ventas_validas = ventas_validas.persist()

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
