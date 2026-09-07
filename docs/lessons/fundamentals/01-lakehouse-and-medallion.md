# Bài 1 — Lakehouse & Medallion Architecture

## Mục tiêu
Nắm được bức tranh tổng thể: dữ liệu đi từ đâu, qua Databricks như thế nào,
ra tới đâu — và thuộc lòng khái niệm Bronze/Silver/Gold.

## Mô hình cơ bản

```
Nguồn dữ liệu
Database / API / Kafka / CSV / JSON
          ↓
      Databricks
          ↓
Bronze → Silver → Gold
          ↓
BI / Dashboard / ML / AI
```

## Ba tầng thường gặp (Medallion Architecture)

- **Bronze**: dữ liệu thô, gần như giữ nguyên. Chỉ thêm metadata (nguồn,
  thời điểm ingest), không làm sạch.
- **Silver**: clean, deduplicate, join, chuẩn hóa kiểu dữ liệu/tên cột.
- **Gold**: dữ liệu business-ready để dashboard/report/ML — thường đã
  tổng hợp (aggregate) theo nhu cầu nghiệp vụ cụ thể.

## Luồng thực tế cần thuộc lòng

Ví dụ công ty có database chứa đơn hàng:

```
PostgreSQL
    ↓
INGEST
    ↓
Bronze (raw_orders)
    ↓
TRANSFORM
    ↓
Silver (clean_orders)
    ↓
AGGREGATE
    ↓
Gold (daily_sales)
    ↓
Power BI / Tableau
```

**Bronze:**
```python
df = spark.read.format("...").load(...)

df.write.format("delta").mode("append").saveAsTable("bronze.orders")
```

**Silver:**
```python
orders = spark.table("bronze.orders")

clean = (
    orders
    .dropDuplicates(["order_id"])
    .filter("amount > 0")
)

clean.write.mode("overwrite").saveAsTable("silver.orders")
```

**Gold:**
```sql
CREATE OR REPLACE TABLE gold.daily_sales AS
SELECT
    DATE(order_time) AS order_date,
    SUM(amount) AS revenue
FROM silver.orders
GROUP BY DATE(order_time);
```

Hiểu được pipeline này là đã hiểu phần lớn use case Data Engineering trên
Databricks.

## Áp dụng vào project

- Data mẫu `nyctaxi` (`samples.nyctaxi.trips`) → `sample_trips_my_project`
  (≈ Bronze/Silver gộp, chỉ copy nguyên) → `sample_zones_my_project`
  (≈ Gold, group by + sum) — xem [architecture.md](../../architecture.md).
  Pipeline này dùng data mẫu tĩnh nên **không cần** thực hành ACID/time
  travel/incremental — lý do cụ thể ở [Bài 11](11-acid-timetravel-incremental.md).
- Bài tập thực hành đầy đủ 3 tầng **trên data thật, đã build + verify chạy
  thật** (nơi 3 khái niệm ở Bài 11 mới thật sự có ý nghĩa): xem
  [roadmap/phase-1-ecommerce.md](../../roadmap/phase-1-ecommerce.md)
  mục 2.3–2.5.
