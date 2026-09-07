# Bronze — order_items, qua Auto Loader (streaming). Đây là bảng fact,
# 92 file thật (1 file/ngày) — Auto Loader tự nhớ file nào đã đọc, chỉ xử
# lý file mới ở mỗi lần refresh. Xem docs/lessons/fundamentals/10-volumes-and-autoloader.md.
from pyspark import pipelines as dp

catalog = spark.conf.get("ecomm_catalog")
RAW_BASE = f"/Volumes/{catalog}/bronze/raw_files"


@dp.table
def bronze_order_items():
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "csv")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("header", "true")
        .load(f"{RAW_BASE}/order_items/landing/")
        .selectExpr("*", "_metadata.file_path as source_file", "current_timestamp() as ingested_at")
    )
