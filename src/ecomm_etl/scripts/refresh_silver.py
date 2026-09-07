"""Silver — Delta Table + Job/Notebook, dùng MERGE INTO cho bảng fact.

KHÔNG qua Lakeflow (không phải @dp.table). Ra bảng TABLE thật. 2 kiểu ghi
khác nhau, chọn theo bản chất data — đúng khung quyết định:
  - 5 dimension: mỗi lần refresh là bản export MỚI NHẤT toàn bộ (không có
    "thay đổi từng dòng" để MERGE) -> CREATE OR REPLACE TABLE, đơn giản
    hơn MERGE mà không mất gì.
  - order_items (fact table): mỗi lần chạy có thể có dòng SỬA/MỚI xen giữa
    dòng cũ đã xử lý -> MERGE INTO theo khóa (order_id, item_seq), đúng
    pattern "ETL đêm lấy data hôm qua rồi MERGE" (SAP-style) mà bạn mô tả.

Xem docs/lessons/fundamentals/13-delta-table-job-vs-lakeflow.md.
"""
import argparse

from delta.tables import DeltaTable
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lower, regexp_replace, round as spark_round, to_date, trim, upper


def refresh_dimensions(spark, catalog: str):
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.silver")

    # silver_brands — Bug 1 (khoảng trắng thừa), Bug 2 (case brand_code
    # khác với products) đã tìm thấy khi khảo sát data thật.
    brands = (
        spark.read.table(f"{catalog}.bronze.bronze_brands")
        .withColumn("brand_code", lower(regexp_replace(trim(col("brand_code")), "[^A-Za-z0-9]", "")))
        .withColumn("brand_name", trim(col("brand_name")))
        .withColumn("category_code", lower(trim(col("category_code"))))
    )
    brands.write.mode("overwrite").saveAsTable(f"{catalog}.silver.silver_brands")

    category = (
        spark.read.table(f"{catalog}.bronze.bronze_category")
        .withColumn("category_code", lower(trim(col("category_code"))))
        .withColumn("category_name", trim(col("category_name")))
    )
    category.write.mode("overwrite").saveAsTable(f"{catalog}.silver.silver_category")

    # silver_date — Bug 3 (case day_name), Bug 4 (week_of_year toàn bộ âm).
    # Không có @dp.expect ở đây (chỉ Lakeflow mới có) — nếu cần validate,
    # tự viết assert/log tay, vd:
    date_df = (
        spark.read.table(f"{catalog}.bronze.bronze_date")
        .withColumn("order_date", to_date(col("date"), "dd-MM-yyyy"))
        .withColumn("day_name", upper(trim(col("day_name"))))
        .withColumn("week_of_year", col("week_of_year").cast("int"))
        .withColumn("year", col("year").cast("int"))
        .withColumn("quarter", col("quarter").cast("int"))
    )
    invalid_weeks = date_df.filter("week_of_year NOT BETWEEN 1 AND 53").count()
    if invalid_weeks:
        print(f"WARNING: silver_date có {invalid_weeks} dòng week_of_year vô lý (không loại, chỉ cảnh báo)")
    date_df.write.mode("overwrite").saveAsTable(f"{catalog}.silver.silver_date")

    # silver_products — Bug 5 (weight_grams "305g"), Bug 6 (length_cm "22,2").
    products = (
        spark.read.table(f"{catalog}.bronze.bronze_products")
        .withColumn("weight_grams", regexp_replace(col("weight_grams"), "[^0-9.]", "").cast("double"))
        .withColumn("length_cm", regexp_replace(col("length_cm"), ",", ".").cast("double"))
        .withColumn("width_cm", regexp_replace(col("width_cm"), ",", ".").cast("double"))
        .withColumn("height_cm", regexp_replace(col("height_cm"), ",", ".").cast("double"))
        .withColumn("brand_code", lower(trim(col("brand_code"))))
        .withColumn("category_code", lower(trim(col("category_code"))))
        .withColumn("rating_count", col("rating_count").cast("int"))
    )
    products.write.mode("overwrite").saveAsTable(f"{catalog}.silver.silver_products")

    customers = spark.read.table(f"{catalog}.bronze.bronze_customers")
    customers.write.mode("overwrite").saveAsTable(f"{catalog}.silver.silver_customers")


def refresh_order_items(spark, catalog: str):
    # Bug 7 (discount_pct "10%") + tính line_total + join star-schema.
    order_items = (
        spark.read.table(f"{catalog}.bronze.bronze_order_items")
        .withColumn("order_date", to_date(col("dt")))
        .withColumn("quantity", col("quantity").cast("int"))
        .withColumn("unit_price", col("unit_price").cast("double"))
        .withColumn("discount_pct", regexp_replace(col("discount_pct"), "%", "").cast("double") / 100)
        .withColumn("tax_amount", col("tax_amount").cast("double"))
        .withColumn(
            "line_total",
            spark_round(col("quantity") * col("unit_price") * (1 - col("discount_pct")) + col("tax_amount"), 2),
        )
    )
    products = spark.read.table(f"{catalog}.silver.silver_products").select("product_id", "brand_code", "category_code")
    brands = spark.read.table(f"{catalog}.silver.silver_brands").select("brand_code", "brand_name")
    category = spark.read.table(f"{catalog}.silver.silver_category").select("category_code", "category_name")

    enriched = (
        order_items.join(products, on="product_id", how="left")
        .join(brands, on="brand_code", how="left")
        .join(category, on="category_code", how="left")
    )

    target = f"{catalog}.silver.silver_order_items"
    if not spark.catalog.tableExists(target):
        enriched.write.format("delta").saveAsTable(target)
        print(f"created {target}: {enriched.count()} rows (lần đầu, chưa có gì để MERGE)")
        return

    # MERGE INTO thật — đúng pattern "ETL đêm lấy data mới rồi MERGE" (SAP-style).
    # Khóa (order_id, item_seq): 1 dòng order_items = 1 item trong 1 order.
    target_table = DeltaTable.forName(spark, target)
    (
        target_table.alias("t")
        .merge(enriched.alias("s"), "t.order_id = s.order_id AND t.item_seq = s.item_seq")
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
    )
    print(f"MERGE xong vào {target}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True)
    args = parser.parse_args()

    spark = SparkSession.builder.getOrCreate()
    refresh_dimensions(spark, args.catalog)
    refresh_order_items(spark, args.catalog)


if __name__ == "__main__":
    main()
