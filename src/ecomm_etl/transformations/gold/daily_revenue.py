# Gold — join 3 bảng + aggregate nặng cho dashboard -> đúng khung quyết
# định, hợp Materialized View (Lakeflow tự refresh, không cần code lại
# refresh logic tay). silver_order_items/silver_date giờ là plain Delta
# Table (ghi bởi refresh_silver.py, không qua Lakeflow) — đọc bình thường
# bằng spark.read.table(), Lakeflow không quan tâm bảng nguồn được tạo
# bằng cách nào, chỉ cần nó tồn tại trong cùng catalog.
from pyspark import pipelines as dp
from pyspark.sql.functions import sum as spark_sum, count, countDistinct


@dp.table
def gold_daily_category_revenue():
    order_items = spark.read.table("silver.silver_order_items")
    date_dim = spark.read.table("silver.silver_date").select(
        "order_date", "day_name", "quarter", "year"
    )

    enriched = order_items.join(date_dim, on="order_date", how="left")

    return (
        enriched.groupBy("order_date", "day_name", "quarter", "year", "category_name", "brand_name")
        .agg(
            spark_sum("line_total").alias("revenue"),
            count("*").alias("line_items"),
            countDistinct("order_id").alias("orders"),
        )
    )
