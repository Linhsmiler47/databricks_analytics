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

`MERGE INTO` chính là cơ chế nằm bên dưới
`dp.create_auto_cdc_from_snapshot_flow(...)` mà bạn dùng ở
[roadmap/phase-1-track1-cdc-demo.md mục 1.5](../../roadmap/phase-1-track1-cdc-demo.md) —
hiểu MERGE trước sẽ hiểu ngay AUTO CDC làm gì, không cần học thuộc lòng.
