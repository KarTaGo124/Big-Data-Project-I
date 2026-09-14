from pathlib import Path

from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, IntegerType, StringType, StructField, StructType

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "online_retail_II.csv"


def print_header(number, title):
    print(f"\n{'=' * 70}")
    print(f"Consulta {number:02d} — {title}")
    print("=" * 70)


def load_raw(spark):
    schema = StructType(
        [
            StructField("Invoice", StringType(), True),
            StructField("StockCode", StringType(), True),
            StructField("Description", StringType(), True),
            StructField("Quantity", IntegerType(), True),
            StructField("InvoiceDate", StringType(), True),
            StructField("Price", DoubleType(), True),
            StructField("Customer ID", DoubleType(), True),
            StructField("Country", StringType(), True),
        ]
    )
    return spark.read.option("header", True).schema(schema).csv(str(DATA_PATH))


def query_01_limpieza(df):
    total_antes = df.count()
    limpio = df.filter(F.col("Description").isNotNull() & (F.col("Price") > 0))
    total_despues = limpio.count()
    print(f"Filas antes: {total_antes}")
    print(f"Filas despues: {total_despues}")
    print(f"Filas eliminadas: {total_antes - total_despues}")
    return limpio


def query_02_duplicados(df):
    total_antes = df.count()
    sin_duplicados = df.dropDuplicates()
    total_despues = sin_duplicados.count()
    print(f"Filas antes: {total_antes}")
    print(f"Filas despues: {total_despues}")
    print(f"Duplicados eliminados: {total_antes - total_despues}")
    return sin_duplicados


def query_03_transformacion(df):
    df = df.withColumn("InvoiceDate", F.to_timestamp("InvoiceDate"))
    df = df.withColumn("TotalPrice", F.col("Quantity") * F.col("Price"))
    df = df.withColumn("IsCancelled", F.col("Invoice").startswith("C"))
    df = df.withColumn("Year", F.year("InvoiceDate"))
    df = df.withColumn("Month", F.month("InvoiceDate"))
    df.select("Invoice", "TotalPrice", "IsCancelled", "Year", "Month").show(5)
    return df


def query_04_filtrado(df):
    total_antes = df.count()
    validas = df.filter(
        (F.col("Quantity") > 0) & (F.col("Price") > 0) & (~F.col("IsCancelled"))
    )
    total_despues = validas.count()
    print(f"Filas antes: {total_antes}")
    print(f"Ventas validas: {total_despues}")
    return validas


def query_05_top_productos_revenue(df):
    top10 = (
        df.groupBy("Description")
        .agg(F.sum("TotalPrice").alias("TotalPrice"))
        .orderBy(F.desc("TotalPrice"))
        .limit(10)
    )
    top10.show(truncate=False)
    return top10


def query_06_top_productos_unidades(df):
    top10 = (
        df.groupBy("Description")
        .agg(F.sum("Quantity").alias("Quantity"))
        .orderBy(F.desc("Quantity"))
        .limit(10)
    )
    top10.show(truncate=False)
    return top10


def query_07_top_clientes(df):
    top10 = (
        df.filter(F.col("Customer ID").isNotNull())
        .groupBy("Customer ID")
        .agg(F.sum("TotalPrice").alias("TotalPrice"))
        .orderBy(F.desc("TotalPrice"))
        .limit(10)
    )
    top10.show()
    return top10


def query_08_revenue_por_pais(df):
    resumen = (
        df.groupBy("Country")
        .agg(
            F.sum("TotalPrice").alias("Revenue"),
            F.countDistinct("Invoice").alias("Facturas"),
        )
        .withColumn("TicketPromedio", F.col("Revenue") / F.col("Facturas"))
        .orderBy(F.desc("Revenue"))
        .limit(10)
    )
    resumen.show(truncate=False)
    return resumen


def query_09_revenue_mensual(df):
    mensual = (
        df.groupBy("Year", "Month")
        .agg(F.sum("TotalPrice").alias("Revenue"))
        .orderBy("Year", "Month")
    )
    ventana = Window.orderBy("Year", "Month")
    mensual = mensual.withColumn(
        "VariacionPct", (F.col("Revenue") / F.lag("Revenue").over(ventana) - 1) * 100
    )
    mensual.show(30)
    return mensual


def query_10_tasa_cancelacion_por_pais(df):
    resumen = (
        df.groupBy("Country")
        .agg(
            F.count("Invoice").alias("Total"),
            F.sum(F.col("IsCancelled").cast("int")).alias("Canceladas"),
        )
        .filter(F.col("Total") >= 30)
        .withColumn("TasaCancelacion", F.col("Canceladas") / F.col("Total") * 100)
        .orderBy(F.desc("TasaCancelacion"))
        .limit(10)
    )
    resumen.show(truncate=False)
    return resumen


def query_11_segmentacion_clientes(df):
    gasto_por_cliente = (
        df.filter(F.col("Customer ID").isNotNull())
        .groupBy("Customer ID")
        .agg(F.sum("TotalPrice").alias("TotalPrice"))
    )
    cortes = gasto_por_cliente.approxQuantile("TotalPrice", [1 / 3, 2 / 3], 0.0)
    tiers = gasto_por_cliente.withColumn(
        "Tier",
        F.when(F.col("TotalPrice") <= cortes[0], "Bajo")
        .when(F.col("TotalPrice") <= cortes[1], "Medio")
        .otherwise("Alto"),
    )
    orden = F.when(F.col("Tier") == "Bajo", 0).when(F.col("Tier") == "Medio", 1).otherwise(2)
    conteo = tiers.groupBy("Tier").count().orderBy(orden)
    conteo.show()
    return conteo


def query_12_ticket_promedio(df):
    revenue_total = df.agg(F.sum("TotalPrice")).first()[0]
    facturas_totales = df.select(F.countDistinct("Invoice")).first()[0]
    aov_global = revenue_total / facturas_totales
    print(f"AOV global: {aov_global:.2f}")

    aov_mensual = (
        df.groupBy("Year", "Month")
        .agg(
            F.sum("TotalPrice").alias("Revenue"),
            F.countDistinct("Invoice").alias("Facturas"),
        )
        .withColumn("AOV", F.col("Revenue") / F.col("Facturas"))
        .orderBy("Year", "Month")
        .select("Year", "Month", "AOV")
    )
    aov_mensual.show(30)
    return aov_global, aov_mensual


def main():
    spark = SparkSession.builder.master("local[*]").appName("online-retail-queries").getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")

    df = load_raw(spark)

    print_header(1, "Limpieza de datos")
    df = query_01_limpieza(df)

    print_header(2, "Eliminacion de duplicados")
    df = query_02_duplicados(df)

    print_header(3, "Transformacion de variables")
    df = query_03_transformacion(df)
    df = df.cache()

    print_header(4, "Filtrado de ventas validas")
    ventas_validas = query_04_filtrado(df)
    ventas_validas = ventas_validas.cache()

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

    spark.stop()


if __name__ == "__main__":
    main()
