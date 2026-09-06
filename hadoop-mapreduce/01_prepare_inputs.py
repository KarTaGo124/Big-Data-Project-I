#!/usr/bin/env python3
"""
Extrae del CSV de retail las dos cosas que necesitan los programas MapReduce.

Lee:    ../data/online_retail_II.csv
Escribe en work/:
  descriptions.txt      <- columna Description, una por linea
  customer_quantity.txt <- columnas "Customer ID" y Quantity, como "id qty"
"""
import csv
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.makedirs("work", exist_ok=True)

with open("../data/online_retail_II.csv", newline="", encoding="utf-8") as f_in, \
     open("work/descriptions.txt", "w", encoding="utf-8") as f_desc, \
     open("work/customer_quantity.txt", "w", encoding="utf-8") as f_qty:

    for row in csv.DictReader(f_in):
        description = row["Description"].strip()
        if description:
            f_desc.write(description + "\n")

        customer_id = row["Customer ID"].strip()
        quantity = row["Quantity"].strip()
        if customer_id and quantity:
            f_qty.write(f"{int(float(customer_id))} {int(float(quantity))}\n")

print("Generados: work/descriptions.txt y work/customer_quantity.txt")
