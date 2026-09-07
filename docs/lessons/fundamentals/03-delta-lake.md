# Bài 3 — Delta Lake

## Mục tiêu
Hiểu Delta Lake là gì và vì sao `MERGE INTO` (pattern upsert) là câu lệnh
quan trọng nhất cần nhớ trong toàn bộ Delta Lake.

## Nội dung

Cách nghĩ đơn giản nhất:

```
Parquet + transaction log = Delta Table
```

Delta cung cấp các khả năng **database-like** trên data lake:
- ACID transactions
- Schema enforcement (chặn ghi sai schema)
- Schema evolution (cho phép schema thay đổi có kiểm soát)
- `UPDATE` / `DELETE` — thứ Parquet thuần không hỗ trợ
- `MERGE` — upsert
- Time travel — query lại data ở version/thời điểm cũ

(Giải thích sâu ACID + Time travel — kể cả khác biệt với SCD Type 2, và
"incremental" nghĩa là gì theo từng layer — xem
[Bài 11](11-acid-timetravel-incremental.md).)

### Pattern hay gặp nhất: MERGE INTO (upsert)

```sql
MERGE INTO silver.customer AS target
USING bronze.customer_update AS source
ON target.id = source.id
WHEN MATCHED THEN
  UPDATE SET *
WHEN NOT MATCHED THEN
  INSERT *
```

Nghĩa là: nếu `id` đã tồn tại → update, chưa tồn tại → insert. Đây chính
là cơ chế nền cho các API cao cấp hơn như AUTO CDC (Lakeflow tự sinh ra
1 câu MERGE tương tự phía dưới, bạn không cần viết tay).

## Áp dụng vào project

`MERGE INTO` chính là cách `refresh_silver.py` cập nhật `silver_order_items`
mỗi lần chạy (upsert theo khóa `order_id, item_seq`) — xem code thật đã
verify chạy ổn định ở
[roadmap/phase-1-ecommerce.md mục 2.4](../../roadmap/phase-1-ecommerce.md).
Đây chính là pattern "ETL đêm rồi MERGE" — hiểu MERGE trước sẽ hiểu ngay
code đó làm gì, không cần học thuộc lòng.
