# Bài 11 — ACID, Time Travel, Incremental: áp dụng vào layer nào

## Mục tiêu
3 khái niệm hay bị học "cho biết tên" mà không hiểu áp dụng ở đâu. Bài này
nối chúng vào đúng layer Bronze/Silver/Gold, và đối chiếu với 2 pipeline
đang có trong repo — 1 cái có data thật đổi liên tục (e-commerce), 1 cái
không cần (nyctaxi demo) — để thấy rõ khi nào mỗi khái niệm thật sự có
ý nghĩa.

## 1. ACID — áp dụng ở **mọi** layer, mọi lúc (không phải chọn dùng hay không)

Mỗi lần 1 table Delta được ghi (bất kể `@dp.table` batch hay streaming),
Delta Lake tự đảm bảo 4 tính chất — không cần bạn code gì thêm:

| Chữ | Nghĩa | Ví dụ cụ thể trong pipeline |
|---|---|---|
| **A**tomicity | Ghi thành công hết hoặc không ghi gì cả, không có nửa vời | `MERGE INTO` trong `refresh_silver.py` áp toàn bộ thay đổi vào `silver_order_items`, hoặc fail hết — không có chuyện chỉ update được 1/3 số dòng |
| **C**onsistency | Table luôn ở trạng thái hợp lệ theo schema đã khai báo | `dp.create_streaming_table` khai schema `id INT, ...` — ghi sai kiểu bị chặn |
| **I**solation | Người đang query table không thấy trạng thái "ghi dở" | Bạn mở Catalog Explorer xem `silver_order_items` giữa lúc job đang chạy — vẫn thấy 1 version hoàn chỉnh, không thấy dữ liệu lỡ dở |
| **D**urability | Đã commit thì không mất, kể cả pipeline crash ngay sau đó | Transaction log (`_delta_log/`) ghi trước, file data ghi sau — crash giữa chừng vẫn khôi phục được đúng trạng thái |

**Không có khái niệm "layer nào cần ACID hơn"** — Bronze, Silver, Gold đều
là Delta table, đều được ACID miễn phí. Đây là lý do dù pipeline `nyctaxi`
chỉ demo tĩnh, nó vẫn "có ACID" — chỉ là không có cơ hội nào để *thấy* lợi
ích đó (không ai ghi đồng thời, không có concurrent write để tránh xung đột).

## 2. Time Travel — khác hẳn SCD Type 2, đừng nhầm

Đây là điểm dễ nhầm nhất: cả 2 đều "xem lại quá khứ", nhưng khác hoàn toàn
về bản chất.

```sql
-- Xem lại đúng dữ liệu ở version 3 của cả bảng
SELECT * FROM ecomm_dev.silver.silver_order_items VERSION AS OF 3;
SELECT * FROM ecomm_dev.silver.silver_order_items TIMESTAMP AS OF '2026-01-02';

-- Xem lịch sử version (chỉ chạy được trên TABLE thật, không phải materialized view — xem Bài 12)
DESCRIBE HISTORY ecomm_dev.silver.silver_order_items;
```

| | Time Travel | SCD Type 2 |
|---|---|---|
| Xem lại cái gì | Toàn bộ **bảng** tại 1 thời điểm ghi (mỗi lần pipeline chạy = 1 version) | Từng **dòng nghiệp vụ** thay đổi thế nào theo thời gian |
| Lưu ở đâu | Transaction log (`_delta_log/`), tách biệt khỏi data | Ngay trong bảng, qua cột `__START_AT`/`__END_AT` |
| Giữ bao lâu | Có hạn — mặc định ~30 ngày rồi bị `VACUUM` dọn | Vĩnh viễn, trừ khi bạn tự xóa |
| Dùng để | Debug/rollback kỹ thuật ("pipeline chạy sai lúc 3h chiều, xem lại trước đó") | Trả lời câu hỏi nghiệp vụ ("khách hàng An hồi tháng 1 dùng email gì") |

→ Time travel là công cụ **kỹ thuật** (an toàn khi debug), SCD Type 2 là
**thiết kế dữ liệu** (chủ động lưu lịch sử nghiệp vụ). Bạn cần cả 2, không
cái nào thay được cái nào.

## 3. Incremental — 3 cơ chế khác nhau theo layer

⚠️ **Hiểu nhầm hay gặp**: "materialized view thì không tự update" — **sai**.
Cả streaming table lẫn materialized view đều **chỉ cập nhật khi pipeline
chạy** (không tự real-time 24/7 — giống nhau ở điểm này). Khác biệt là
**cách** nó cập nhật khi chạy:

| | Streaming table | Materialized view |
|---|---|---|
| Xử lý gì mỗi lần refresh | Chỉ dòng **mới** (checkpoint nhớ đã đọc gì) | Tính lại để khớp đúng **toàn bộ** data nguồn hiện tại |
| Có sửa lại dòng cũ khi nguồn đổi không | Không — append-only, dòng cũ coi như xong | **Có** — dòng cũ tự cập nhật theo nếu nguồn đổi |
| Hợp cho | Ingest thô, fact table (chỉ tăng dần) | Join/aggregate — cần đúng với toàn bộ state, kể cả khi dimension cũ bị sửa |

**Bằng chứng thật** (không phải lý thuyết): gotcha `expect_or_drop` ở
[roadmap phase-1-ecommerce.md mục 2.4](../../roadmap/phase-1-ecommerce.md) —
lần chạy đầu `gold_daily_category_revenue.day_name` NULL 100%; sau khi sửa
code + chạy lại `ecomm_job` **lần 2**, `day_name` tự đúng hết, không cần
xóa bảng thủ công. Materialized view **tự tính lại** đúng data mới nhất
mỗi lần pipeline refresh — đó chính là ý nghĩa "incremental" ở layer này:
không phải "không đổi", mà là engine cố tính lại **hiệu quả** (chỉ phần bị
ảnh hưởng khi có thể) thay vì luôn quét lại từ đầu một cách ngu ngơ.

| Layer (điển hình) | Loại bảng | Cơ chế incremental |
|---|---|---|
| Bronze (fact, vd `order_items`) | **Streaming table** (Lakeflow, `spark.readStream` + Auto Loader) | Checkpoint nhớ file nào đã đọc — chỉ đọc file mới (xem [Bài 10](10-volumes-and-autoloader.md)) |
| Bronze (dimension) / Silver | **Plain Delta Table** (script + Job, không qua Lakeflow) | Tự viết logic: `CREATE OR REPLACE TABLE` (full refresh, hợp dimension) hoặc `MERGE INTO` (upsert theo khóa, hợp fact table) — xem [Bài 13](13-delta-table-job-vs-lakeflow.md) |
| Gold | **Materialized view** (Lakeflow, `@dp.table` đọc batch, có filter/aggregate) | Engine tự tính lại phần bị ảnh hưởng khi source đổi, không phải luôn full recompute — nhưng **luôn phản ánh đúng data mới nhất** sau mỗi lần refresh |

Nguồn: [Best practices — Lakeflow Declarative Pipelines](https://docs.databricks.com/aws/en/ldp/best-practices).

## Áp dụng vào 2 pipeline trong repo — so sánh trực tiếp

| | `nyctaxi` demo (có sẵn từ template) | e-commerce (project chính, đã verify chạy thật) |
|---|---|---|
| ACID | Có (mọi Delta table đều có), nhưng không có tình huống nào để *thấy* rõ | Có — quan trọng thật sự vì `silver_order_items` bị `MERGE` nhiều lần |
| Time travel | Chạy được về mặt kỹ thuật, nhưng vô nghĩa vì source `samples.nyctaxi.trips` không đổi | Hữu ích thật — `silver_order_items` là TABLE thật, `DESCRIBE HISTORY`/`VERSION AS OF` chạy được (khác `gold_daily_category_revenue`, là materialized view — xem [Bài 12](12-permissions-hierarchy-and-abac.md)) |
| Incremental | Có tồn tại về mặt kỹ thuật (2 bảng đều Lakeflow) nhưng không có gì "mới" để tăng dần — source tĩnh | Có ý nghĩa thật — `bronze_order_items` incremental qua Auto Loader, `silver_order_items` incremental qua `MERGE INTO` (đã verify idempotent qua 3 lần chạy liên tiếp, không nhân đôi dòng) |

→ Đúng như nhận định ban đầu: pipeline `nyctaxi` **skip phần thực hành 3
khái niệm này là hợp lý**, vì nó dùng data mẫu tĩnh. Project e-commerce
mới là nơi cả 3 khái niệm này thật sự "sống" — xem
[roadmap/phase-1-ecommerce.md](../../roadmap/phase-1-ecommerce.md).

> 📌 **Về SCD Type 2**: khái niệm ở mục 2 (bảng so sánh Time Travel vs
> SCD2) vẫn đúng và đáng nhớ cho phỏng vấn/thiết kế hệ thống — nhưng repo
> này hiện **không còn ví dụ chạy thật** cho SCD Type 2 (từng có 1 case
> study CDC/SCD2 nhỏ, đã gỡ bỏ vì project e-commerce đã đủ end-to-end).
> Muốn thực hành lại: dùng đúng API `dp.create_auto_cdc_from_snapshot_flow(...,
> stored_as_scd_type=2)` đã nhắc ở mục 2, áp lên 1 bảng bất kỳ có dữ liệu
> thay đổi theo thời gian.

## Áp dụng cụ thể vào project

- [roadmap/phase-1-ecommerce.md mục 2.3](../../roadmap/phase-1-ecommerce.md) —
  `bronze_order_items` = streaming table, incremental qua Auto Loader.
- [mục 2.4](../../roadmap/phase-1-ecommerce.md) —
  `silver_order_items` = plain Delta Table, incremental qua `MERGE INTO`
  tự viết (không qua Lakeflow — xem [Bài 13](13-delta-table-job-vs-lakeflow.md)).
- [mục 2.5](../../roadmap/phase-1-ecommerce.md) —
  `gold_daily_category_revenue` = materialized view (Lakeflow), incremental
  qua engine tự tính lại phần đổi.
- Bài tập gợi ý thêm (chưa có trong roadmap, tự làm nếu muốn): chạy
  `DESCRIBE HISTORY ecomm_dev.silver.silver_order_items` sau vài lần chạy
  job, thử `VERSION AS OF` để xem lại 1 version cũ.
