# Bài 2 — Apache Spark cơ bản

## Mục tiêu
Đọc hiểu và tự viết được các đoạn PySpark cơ bản, hiểu vì sao Spark "lười"
(lazy) — đây là khái niệm hay bị hỏi sai nhất khi mới học.

## Nội dung

Databricks xây phần lớn workload data engineering quanh Spark. Chỉ cần
hiểu: **Spark DataFrame ≈ bảng dữ liệu distributed** (chia nhỏ, xử lý song
song trên nhiều máy).

```python
df = spark.read.table("sales.orders")

df2 = (
    df.filter("status = 'completed'")
      .groupBy("customer_id")
      .sum("amount")
)

df2.write.mode("overwrite").saveAsTable("sales.customer_revenue")
```

### Các operation cần nhớ
`select`, `filter`, `withColumn`, `groupBy`, `agg`, `join`, `orderBy`,
`dropDuplicates`.

### Quan trọng nhất: Transformation vs Action

- **Transformation** → lazy (không chạy ngay), vd:
  ```python
  df.filter(...).select(...)   # chưa nhất thiết chạy ngay
  ```
- **Action** → trigger computation thật sự, vd:
  ```python
  df.count()
  df.collect()
  df.write...
  ```

Spark chỉ thật sự đọc/xử lý data khi gặp 1 Action — nó gộp hết các
Transformation phía trước lại thành 1 kế hoạch thực thi tối ưu (query
plan) rồi chạy 1 lần. Đây là lý do vì sao viết nhiều `.filter().select()`
liên tiếp không tốn thêm chi phí gì cho tới khi có Action.

## Áp dụng vào project

- [src/my_project/taxis.py](../../../src/my_project/taxis.py) —
  `find_all_taxis()` chỉ là 1 Transformation (`spark.read.table`), thật sự
  chạy khi `main.py` gọi `.show(5)` (Action).
- [src/my_project_etl/transformations/sample_zones_my_project.py](../../../src/my_project_etl/transformations/sample_zones_my_project.py) —
  ví dụ `groupBy().agg(sum(...))` thật trong repo.
