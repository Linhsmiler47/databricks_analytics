"""Bronze — 5 dimension table, Delta Table + Job/Notebook (KHÔNG qua Lakeflow).

Đây KHÔNG phải @dp.table — là plain PySpark script chạy qua
`spark_python_task` trong resources/ecomm_job.job.yml. Ra bảng thật
(TABLE, không phải MATERIALIZED_VIEW) — vì đây là data "export lại toàn bộ
mỗi lần" (giống 1 dimension export từ hệ thống nguồn mỗi đêm), nên refresh
bằng CREATE OR REPLACE TABLE là hợp lý nhất, không cần MERGE (không có gì
để "hợp nhất" khi cả bảng luôn là bản mới nhất).

Không làm sạch gì ở đây (đúng nguyên tắc Bronze) — giữ nguyên data lỗi,
để Silver xử lý (xem docs/roadmap/phase-1-track2-ecommerce-project.md).

Xem [Bài 13 — Delta Table + Job vs Streaming Table vs Materialized View]
(docs/lessons/fundamentals/13-delta-table-job-vs-lakeflow.md) để biết vì
sao chọn cách này thay vì @dp.table.
"""
import argparse

from pyspark.sql import SparkSession

DIMENSIONS = ["brands", "category", "date", "products", "customers"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True)
    args = parser.parse_args()

    spark = SparkSession.builder.getOrCreate()
    raw_base = f"/Volumes/{args.catalog}/bronze/raw_files"

    for name in DIMENSIONS:
        df = spark.read.option("header", True).csv(f"{raw_base}/{name}/{name}.csv")
        df.write.mode("overwrite").saveAsTable(f"{args.catalog}.bronze.bronze_{name}")
        print(f"refreshed {args.catalog}.bronze.bronze_{name}: {df.count()} rows")


if __name__ == "__main__":
    main()
