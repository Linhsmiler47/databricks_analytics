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
from pyspark.sql.functions import col, expr, lower, regexp_replace, round as spark_round, to_date, trim, upper


def refresh_dimensions(spark, catalog: str):
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.silver")

    # silver_brands — Bug 1 (khoảng trắng thừa), Bug 2 (case brand_code
    # khác với products) đã tìm thấy khi khảo sát data thật.
    brands = (
        spark.read.table(f"{catalog}.bronze.bronze_brands")
        .withColumn("brand_code", lower(regexp_replace(trim(col("brand_code")), "[^A-Za-z0-9]", "")))
        .withColumn("brand_name", trim(col("brand_name")))
        .withColumn("category_code", lower(trim(col("category_code"))))
        # Bug 10 (phòng ngừa): dropDuplicates theo khóa nghiệp vụ — Silver
        # là "đã làm sạch", không nên còn dòng trùng dù join có tự dedupe
        # riêng hay không. Nguồn dùng làm bằng chứng: xem category bên dưới.
        .dropDuplicates(["brand_code"])
    )
    brands.write.mode("overwrite").saveAsTable(f"{catalog}.silver.silver_brands")

    # Bug 10 (thật, đã tìm thấy khi MERGE fail với
    # DELTA_MULTIPLE_SOURCE_ROW_MATCHING_TARGET_ROW_IN_MERGE): bronze_category
    # có dòng TRÙNG LẶP y hệt trong CSV gốc (vd "app"/"Apparel" xuất hiện 2
    # lần) — dropDuplicates ngay tại đây, không chỉ ở chỗ join, vì
    # silver_category tự nó phải sạch (ai query trực tiếp bảng này cũng
    # không nên thấy dòng trùng).
    category = (
        spark.read.table(f"{catalog}.bronze.bronze_category")
        .withColumn("category_code", lower(trim(col("category_code"))))
        .withColumn("category_name", trim(col("category_name")))
        .dropDuplicates(["category_code"])
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
        .dropDuplicates(["product_id"])  # phòng ngừa, cùng lý do Bug 10
    )
    products.write.mode("overwrite").saveAsTable(f"{catalog}.silver.silver_products")

    customers = spark.read.table(f"{catalog}.bronze.bronze_customers")
    customers.write.mode("overwrite").saveAsTable(f"{catalog}.silver.silver_customers")


def refresh_order_items(spark, catalog: str):
    # Bug 7 (discount_pct "10%"). Bug 8 (quantity có giá trị chữ, vd "Two"
    # thay vì 2 — 33,138/183,378 dòng, ~18%!). Bug 9 (unit_price có ký hiệu
    # tiền tệ, vd "$864"). Cả 3 cột số đều không tin tưởng được — plain
    # .cast() CHẾT CỨNG cả job ngay dòng đầu tiên gặp rác. Dùng chung 1 rule
    # phòng thủ: bóc hết ký tự không phải số/dấu chấm/trừ rồi try_cast, lọc
    # bỏ dòng nào sau cùng vẫn NULL (không đoán mò giá trị thay thế).
    def _clean_numeric(colname: str):
        return expr(f"try_cast(regexp_replace({colname}, '[^0-9.-]', '') AS DOUBLE)")

    raw_order_items = spark.read.table(f"{catalog}.bronze.bronze_order_items")
    total_rows = raw_order_items.count()
    order_items = (
        raw_order_items
        .withColumn("order_date", to_date(col("dt")))
        .withColumn("quantity", expr("try_cast(quantity AS INT)"))
        .withColumn("unit_price", _clean_numeric("unit_price"))
        .withColumn("discount_pct", _clean_numeric("regexp_replace(discount_pct, '%', '')") / 100)
        .withColumn("tax_amount", _clean_numeric("tax_amount"))
    )
    required = ["quantity", "unit_price", "discount_pct", "tax_amount"]
    order_items_clean = order_items.na.drop(subset=required)
    dropped = total_rows - order_items_clean.count()
    if dropped:
        print(f"WARNING: loại {dropped}/{total_rows} dòng order_items có cột số hỏng (quantity/unit_price/discount_pct/tax_amount không parse được)")
    order_items = (
        order_items_clean
        .withColumn(
            "line_total",
            spark_round(col("quantity") * col("unit_price") * (1 - col("discount_pct")) + col("tax_amount"), 2),
        )
    )
    # Bug 10: bronze_category có DÒNG TRÙNG LẶP y hệt (vd "app"/"Apparel"
    # xuất hiện 2 lần trong CSV gốc) — join bình thường sẽ nhân đôi dòng
    # order_items khớp category đó, làm MERGE bên dưới fail với
    # DELTA_MULTIPLE_SOURCE_ROW_MATCHING_TARGET_ROW_IN_MERGE. dropDuplicates
    # theo khóa nghiệp vụ trước khi join — áp phòng ngừa cho cả 3 dimension,
    # không chỉ category (rẻ, an toàn, chặn đứng cả lớp bug này).
    products = (
        spark.read.table(f"{catalog}.silver.silver_products")
        .select("product_id", "brand_code", "category_code")
        .dropDuplicates(["product_id"])
    )
    brands = (
        spark.read.table(f"{catalog}.silver.silver_brands")
        .select("brand_code", "brand_name")
        .dropDuplicates(["brand_code"])
    )
    category = (
        spark.read.table(f"{catalog}.silver.silver_category")
        .select("category_code", "category_name")
        .dropDuplicates(["category_code"])
    )

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
