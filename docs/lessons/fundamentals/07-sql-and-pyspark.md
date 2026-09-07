# Bài 7 — SQL + PySpark

## Mục tiêu
Đây là 2 skill ROI cao nhất trên Databricks — luyện tới mức viết được mà
không cần tra cứu cú pháp cơ bản.

## SQL cần khá

`SELECT`, `JOIN`, `GROUP BY`, `CTE`, `WINDOW FUNCTION`, `MERGE`,
`CASE WHEN`.

```sql
WITH revenue AS (
    SELECT
        customer_id,
        SUM(amount) AS revenue
    FROM silver.orders
    GROUP BY customer_id
)
SELECT *
FROM revenue
ORDER BY revenue DESC;
```

## PySpark cần khoảng

```python
from pyspark.sql.functions import *

df = spark.table("silver.orders")

result = (
    df
    .filter(col("status") == "completed")
    .groupBy("customer_id")
    .agg(sum("amount").alias("revenue"))
)
```

Đây thực chất là cùng 1 logic viết bằng 2 ngôn ngữ khác nhau — quen 1 bên
sẽ đọc hiểu bên kia rất nhanh.

## Áp dụng vào project

- [tests/sample_taxis_test.py](../../../tests/sample_taxis_test.py) và
  [src/my_project_etl/transformations/sample_zones_my_project.py](../../../src/my_project_etl/transformations/sample_zones_my_project.py) —
  ví dụ PySpark thật (`groupBy`, `agg`, `sum`) đang chạy trong repo.
- [src/ecomm_etl/scripts/refresh_silver.py](../../../src/ecomm_etl/scripts/refresh_silver.py) —
  `MERGE INTO` thật (Delta API `DeltaTable.merge()`), join star-schema, đã
  verify chạy ổn định — xem [roadmap/phase-1-ecommerce.md](../../roadmap/phase-1-ecommerce.md).
