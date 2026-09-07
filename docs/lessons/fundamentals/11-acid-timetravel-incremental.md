# Bài 11 — ACID, Time Travel, Incremental: áp dụng vào layer nào

## Mục tiêu
3 khái niệm hay bị học "cho biết tên" mà không hiểu áp dụng ở đâu. Bài này
nối chúng vào đúng layer Bronze/Silver/Gold, và đối chiếu với 2 pipeline
đang có trong repo — 1 cái được (customers CDC), 1 cái không cần (nyctaxi
demo) — để thấy rõ khi nào mỗi khái niệm thật sự có ý nghĩa.

## 1. ACID — áp dụng ở **mọi** layer, mọi lúc (không phải chọn dùng hay không)

Mỗi lần 1 table Delta được ghi (bất kể `@dp.table` batch hay streaming),
Delta Lake tự đảm bảo 4 tính chất — không cần bạn code gì thêm:

| Chữ | Nghĩa | Ví dụ cụ thể trong pipeline |
|---|---|---|
| **A**tomicity | Ghi thành công hết hoặc không ghi gì cả, không có nửa vời | `create_auto_cdc_from_snapshot_flow` áp toàn bộ thay đổi của 1 snapshot vào Silver, hoặc fail hết — không có chuyện chỉ update được 1/3 số dòng |
| **C**onsistency | Table luôn ở trạng thái hợp lệ theo schema đã khai báo | `create_streaming_table` khai schema `id INT, ...` — ghi sai kiểu bị chặn |
| **I**solation | Người đang query table không thấy trạng thái "ghi dở" | Bạn mở Catalog Explorer xem `silver_customers` giữa lúc pipeline đang chạy — vẫn thấy 1 version hoàn chỉnh, không thấy dữ liệu lỡ dở |
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
SELECT * FROM workspace.<schema>.silver_customers VERSION AS OF 3;
SELECT * FROM workspace.<schema>.silver_customers TIMESTAMP AS OF '2026-01-02';

-- Xem lịch sử version
DESCRIBE HISTORY workspace.<schema>.silver_customers;
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
[roadmap Track 2 mục 2.4](../../roadmap/phase-1-track2-ecommerce-project.md) —
lần chạy đầu `gold_daily_category_revenue.day_name` NULL 100%; sau khi sửa
code + chạy lại `ecomm_job` **lần 2**, `day_name` tự đúng hết, không cần
xóa bảng thủ công. Materialized view **tự tính lại** đúng data mới nhất
mỗi lần pipeline refresh — đó chính là ý nghĩa "incremental" ở layer này:
không phải "không đổi", mà là engine cố tính lại **hiệu quả** (chỉ phần bị
ảnh hưởng khi có thể) thay vì luôn quét lại từ đầu một cách ngu ngơ.

| Layer (điển hình) | Loại bảng | Cơ chế incremental |
|---|---|---|
| Bronze | **Streaming table** (`spark.readStream` + Auto Loader) | Checkpoint nhớ file nào đã đọc — chỉ đọc file mới (xem [Bài 10](10-volumes-and-autoloader.md)) |
| Silver | **Streaming table** + AUTO CDC flow | Chỉ áp dụng thay đổi (MERGE) của snapshot/batch mới, không quét lại toàn bộ lịch sử |
| Gold | **Materialized view** (`@dp.table` đọc batch, có filter/aggregate) | Engine tự tính lại phần bị ảnh hưởng khi source đổi, không phải luôn full recompute — nhưng **luôn phản ánh đúng data mới nhất** sau mỗi lần refresh |

Nguồn: [Best practices — Lakeflow Declarative Pipelines](https://docs.databricks.com/aws/en/ldp/best-practices).

## Áp dụng vào 2 pipeline trong repo — so sánh trực tiếp

| | `nyctaxi` demo (có sẵn từ template) | `customers` CDC (đang build, Phase 1) |
|---|---|---|
| ACID | Có (mọi Delta table đều có), nhưng không có tình huống nào để *thấy* rõ | Có — quan trọng thật sự vì Silver bị ghi nhiều lần (mỗi snapshot) |
| Time travel | Chạy được về mặt kỹ thuật, nhưng vô nghĩa vì source `samples.nyctaxi.trips` không đổi | Hữu ích thật — debug xem Silver trông ra sao *trước* khi bạn lỡ upload nhầm 1 snapshot |
| SCD Type 2 | Không áp dụng — pipeline chỉ copy + aggregate 1 lần, không track thay đổi | Trung tâm của case study — `silver_customers` chính là SCD2 |
| Incremental | Có tồn tại về mặt kỹ thuật (2 bảng đều Lakeflow) nhưng không có gì "mới" để tăng dần — source tĩnh | Có ý nghĩa thật — mỗi snapshot mới upload là 1 batch incremental thật sự |

→ Đúng như bạn nói: **pipeline `nyctaxi` skip phần thực hành 3 khái niệm
này là hợp lý**, vì nó dùng data mẫu tĩnh, không có gì biến đổi để mà
"tăng dần" hay "xem lại quá khứ" có ý nghĩa. Nhưng về mặt kỹ thuật, nó vẫn
nằm trên nền tảng Delta có đủ cả 3 — chỉ là không có bài tập nào khai thác
được. Pipeline `customers` (case study Phase 1) mới là nơi cả 3 khái niệm
này thật sự "sống".

## Áp dụng cụ thể vào Phase 1 đang build

- [roadmap/phase-1-track1-cdc-demo.md mục 1.4](../../roadmap/phase-1-track1-cdc-demo.md) —
  `bronze_customers` = streaming table, incremental qua Auto Loader.
- [mục 1.5](../../roadmap/phase-1-track1-cdc-demo.md) — `silver_customers` =
  streaming table qua AUTO CDC, incremental qua MERGE; đồng thời là nơi
  SCD Type 2 thật sự chạy.
- [mục 1.6](../../roadmap/phase-1-track1-cdc-demo.md) — `gold_customers_current`
  = materialized view (batch filter `__END_AT IS NULL`), incremental qua
  engine tự tính lại phần đổi.
- Bài tập gợi ý thêm (chưa có trong roadmap, tự làm nếu muốn): chạy
  `DESCRIBE HISTORY` trên `silver_customers` sau vài lần deploy, thử
  `VERSION AS OF` để xem lại 1 version cũ — so sánh cảm giác với việc query
  `WHERE __END_AT IS NULL` (SCD2) để tự thấy rõ khác biệt.
