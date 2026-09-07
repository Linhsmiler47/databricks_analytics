# Bài 6 — Gotchas thực chiến (đã gặp thật, không phải lý thuyết)

## Mục tiêu
Nhớ trước các lỗi phổ biến nhất khi mới dùng bundle, để không tốn công dò
lại lần sau.

## 1. `SCHEMA_NOT_FOUND` khi chạy job/pipeline lần đầu

**Triệu chứng:** `bundle deploy` chạy OK, nhưng `bundle run` fail:
```
[SCHEMA_NOT_FOUND] The schema `workspace`.`<username>` cannot be found.
```

**Nguyên nhân:** notebook/job dùng `USE SCHEMA` giả định schema đã tồn tại
sẵn — nhưng workspace mới (hoặc target mới) thì chưa có schema đó.

**Cách fix:** tạo schema trước khi chạy lần đầu ở 1 target mới:
```sql
CREATE SCHEMA IF NOT EXISTS workspace.<schema_name>;
```
(hoặc qua Python: `spark.sql("CREATE SCHEMA IF NOT EXISTS ...")` bằng
databricks-connect).

## 2. Đổi sang workspace khác (tạo account Free Edition mới) — 3 bước dễ quên

1. **Đổi host cho profile đã tồn tại**: sửa thẳng dòng `host` trong
   `~/.databrickscfg`, rồi `databricks auth login --profile <name>`
   **không kèm** `--host` — vì kèm `--host` khác với host cũ đã lưu sẽ báo
   lỗi conflict (`--profile "X" has host "...", which conflicts with --host "..."`).
2. **Xóa bundle state cache cũ**: `.databricks/bundle/<target>/` (local,
   gitignored) lưu resource ID của lần deploy trước. Nếu không xóa,
   `bundle deploy` vào workspace mới sẽ cố "đọc" resource theo ID cũ và
   fail `403 PERMISSION_DENIED`. Xóa bằng `rm -rf .databricks/bundle/`
   trước khi deploy lại vào workspace khác.
3. **Update lại mọi chỗ hardcode host/email cũ** trong `databricks.yml`,
   `README.md`, và các file docs khác — grep toàn repo theo host cũ để
   không sót.

## Áp dụng vào project

Cả 2 gotcha trên đã xảy ra thật với repo này. Gotcha #1 (schema not found)
lặp lại ngay trong bước setup — xem [../../setup.md](../../setup.md) và
[roadmap/phase-1-ecommerce.md](../../roadmap/phase-1-ecommerce.md).
Gotcha #2 (đổi workspace) chỉ cần khi bạn thật sự đổi account/workspace.
