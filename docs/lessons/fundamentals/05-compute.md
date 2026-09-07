# Bài 5 — Compute

## Mục tiêu
Biết code/query của bạn thực sự chạy trên loại compute nào, và khác biệt
giữa luồng "chạy notebook" và luồng "chạy BI/SQL".

## Nội dung

Code của bạn cần compute để chạy. 4 loại chính hay gặp:
- **Serverless compute** — Databricks tự quản lý, khởi động nhanh.
- **Classic compute** — cluster bạn tự cấu hình (size, autoscale...).
- **SQL Warehouse** — compute chuyên cho truy vấn SQL/BI.
- **Job compute** — cluster tạo riêng cho 1 lần chạy job, tự hủy sau khi xong.

### Luồng notebook / data engineering

```
Notebook
   ↓
Compute
   ↓
Spark
   ↓
Delta tables
```

### Luồng BI / SQL analytics

```
BI / SQL Editor
      ↓
SQL Warehouse
      ↓
Delta tables
```

Databricks SQL chạy trên SQL warehouses và hỗ trợ ANSI SQL cùng các
extension của Delta Lake.

## Áp dụng vào project

Free Edition **chỉ có serverless compute** (không tạo được Classic
cluster, không GPU) — xem
[operations/01-free-edition-limitations.md](../operations/01-free-edition-limitations.md).
Toàn bộ job/pipeline trong repo này (`databricks bundle run`) đang chạy
trên serverless.
