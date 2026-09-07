# Bài 13 — Delta Table + Job vs Lakeflow (Streaming Table / Materialized View)

## Mục tiêu
Biết khi nào KHÔNG nên dùng Lakeflow Declarative Pipelines mà quay về
cách "cũ hơn" — Job + Notebook/script tự viết `saveAsTable`/`MERGE INTO`.
Nhiều dự án thật (kể cả dự án doanh nghiệp) vẫn dùng cách này làm mặc
định, không phải vì lạc hậu mà vì nó **đơn giản, dễ debug, không ép buộc**
vào 1 trong 2 loại object của Lakeflow.

## Khung quyết định — 3 case điển hình

| Khách nói | Nghĩa là | Chọn |
|---|---|---|
| "Mỗi đêm 2h chạy ETL, lấy data SAP hôm qua rồi MERGE" | Batch định kỳ, có khóa để upsert | **Delta Table + Job/Notebook**, tự viết `MERGE INTO` |
| "Kafka hàng ngàn event/giây, cần xử lý liên tục" | Nguồn liên tục sinh dữ liệu mới, không có "hôm qua" rõ ràng | **Streaming Table** (Lakeflow, Auto Loader/Structured Streaming) |
| "Gold query join 10 bảng, aggregate nặng, dashboard cứ chạy lại" | Cần 1 bảng luôn khớp với toàn bộ data nguồn, không muốn tự viết lại logic refresh | **Materialized View** (Lakeflow) |

Không có "công nghệ đúng cho mọi trường hợp" — 1 project thật (kể cả demo
trong repo này) thường **trộn cả 3**, chọn theo bản chất từng bảng, không
theo thói quen hay theo tutorial đầu tiên bạn học.

## Vì sao 1 dự án thật hay thấy "chỉ có Delta Table + Job + Notebook"

Nhiều dự án doanh nghiệp (đặc biệt dự án cũ hơn, hoặc built trước khi
Lakeflow phổ biến) build 100% bằng Job + Notebook, không dùng
`@dp.table`/Lakeflow chút nào. Đây là lựa chọn hợp lệ, không phải thiếu
sót — nhất là khi:
- Data đa số là batch nightly (giống case SAP) — không có nhu cầu
  streaming/materialized view thật sự.
- Team quen kiểm soát 100% logic refresh bằng tay (dễ debug bằng cách đọc
  thẳng code Python, không cần hiểu thêm framework Lakeflow).
- Lineage hiện trong Catalog Explorer dạng "Job → Notebook → path → query
  → table" (đúng như bạn mô tả) — đây chính là dấu hiệu nhận biết: không
  có "Pipeline" nào trong lineage, nghĩa là không dùng Lakeflow.

## So sánh nhanh 3 loại object

| | Delta Table (Job/Notebook) | Streaming Table (Lakeflow) | Materialized View (Lakeflow) |
|---|---|---|---|
| Ai viết logic refresh | Bạn (tự `saveAsTable`/`MERGE INTO`) | Lakeflow (bạn chỉ khai báo nguồn) | Lakeflow (bạn chỉ khai báo query) |
| Loại object trong UC (`DESCRIBE EXTENDED`) | `TABLE` | `STREAMING_TABLE` | `MATERIALIZED_VIEW` |
| Row Filter/Mask kiểu cũ (`ALTER TABLE SET ROW FILTER`) | ✅ | ✅ | ❌ (phải dùng ABAC, xem [Bài 12](12-permissions-hierarchy-and-abac.md)) |
| Data quality expectations (`@dp.expect_*`) | ❌ (tự viết assert/log tay) | ✅ | ✅ |
| Dependency graph tự động | ❌ (tự khai `depends_on` trong job) | ✅ (trong cùng pipeline) | ✅ (trong cùng pipeline) |
| Tự sửa lại dòng cũ khi nguồn đổi | Tùy bạn viết (MERGE thì có, overwrite thì có, append thì không) | Không (append-only) | Có (tự động, mỗi lần refresh) |

## Áp dụng vào project

Repo này minh họa cả 2 hướng, cạnh nhau, chọn theo đúng khung quyết định:
- [roadmap/phase-1-ecommerce.md](../../roadmap/phase-1-ecommerce.md)
  mục 2.3 — `bronze_order_items` (Streaming Table, case "nguồn liên tục")
  cạnh `refresh_bronze_dimensions.py` (Delta Table + Job, case "SAP nightly").
- Mục 2.4 — `refresh_silver.py`, dùng `MERGE INTO` thật cho
  `silver_order_items` (upsert theo `order_id, item_seq`).
- Mục 2.5 — `gold_daily_category_revenue` vẫn Materialized View (case
  "dashboard aggregate nặng").

## Đọc thêm
- [Best practices for Lakeflow Spark Declarative Pipelines](https://docs.databricks.com/aws/en/ldp/best-practices)
