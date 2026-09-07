# Bài 9 — Ôn phỏng vấn & lộ trình học cấp tốc

## Mục tiêu
Tự test lại toàn bộ 8 bài trước bằng 15 câu hỏi, và có 1 lộ trình rút gọn
8 tiếng nếu cần ôn gấp.

## 15 câu phỏng vấn Databricks phải trả lời được

1. Databricks là gì?
2. Lakehouse là gì?
3. Spark là gì?
4. DataFrame là gì?
5. Transformation vs Action?
6. Lazy evaluation là gì?
7. Partition là gì?
8. Shuffle là gì?
9. Delta Lake là gì?
10. Delta vs Parquet?
11. `MERGE INTO` dùng làm gì?
12. Bronze / Silver / Gold là gì?
13. Unity Catalog là gì?
14. Cluster/compute và SQL Warehouse khác nhau thế nào?
15. Làm thế nào optimize một Spark job chậm?

Trả lời được 15 câu này là đã có khung kiến thức Databricks khá tốt. Map
câu hỏi → bài học nếu quên:

| Câu hỏi | Xem lại |
|---|---|
| 1–2 | [01-lakehouse-and-medallion.md](01-lakehouse-and-medallion.md) |
| 3–6 | [02-spark-fundamentals.md](02-spark-fundamentals.md) |
| 7–8 | [08-performance-and-partitioning.md](08-performance-and-partitioning.md) |
| 9–11 | [03-delta-lake.md](03-delta-lake.md) |
| 12 | [01-lakehouse-and-medallion.md](01-lakehouse-and-medallion.md) |
| 13 | [04-unity-catalog.md](04-unity-catalog.md) |
| 14 | [05-compute.md](05-compute.md) |
| 15 | [08-performance-and-partitioning.md](08-performance-and-partitioning.md) |

## Học cấp tốc trong 1 ngày (8 tiếng)

| Giờ | Nội dung | Bài tương ứng |
|---|---|---|
| 1 | Databricks architecture | [01](01-lakehouse-and-medallion.md) |
| 2 | Spark fundamentals | [02](02-spark-fundamentals.md) |
| 3 | PySpark DataFrame | [02](02-spark-fundamentals.md), [07](07-sql-and-pyspark.md) |
| 4 | Delta Lake | [03](03-delta-lake.md) |
| 5 | Bronze/Silver/Gold pipeline | [01](01-lakehouse-and-medallion.md) |
| 6 | Unity Catalog | [04](04-unity-catalog.md) |
| 7 | Lakeflow Jobs + SQL Warehouse | [05](05-compute.md), [06](06-lakeflow-jobs-pipelines.md) |
| 8 | Spark optimization + câu hỏi phỏng vấn | [08](08-performance-and-partitioning.md), bài này |

**Không nên mất thời gian ban đầu vào** (trừ khi công việc cần trực tiếp):
MLflow, Mosaic AI, Streaming nâng cao, Spark internals sâu, Terraform,
Networking, Admin.

## Thứ tự vàng để nhớ

```
SQL
 ↓
Spark / PySpark
 ↓
Delta Lake
 ↓
Bronze-Silver-Gold
 ↓
Unity Catalog
 ↓
Lakeflow Jobs
 ↓
Performance
```
