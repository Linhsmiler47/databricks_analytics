# Bài 12 — Phân quyền từ cao xuống thấp: hierarchy + 2 cơ chế Row Filter/Mask

## Mục tiêu
Biết đủ 7 tầng phân quyền trong Databricks (không chỉ Unity Catalog), và
phân biệt **2 cơ chế khác nhau** để filter dòng/che cột — vì chọn sai cơ
chế sẽ fail âm thầm trên nhiều loại bảng.

## 7 tầng, từ cao xuống thấp

| # | Tầng | Kiểm soát gì | Ví dụ lệnh/khái niệm |
|---|---|---|---|
| 1 | **Account** | Toàn bộ Databricks account — ai là account admin, có bao nhiêu workspace, account groups (dùng chung mọi workspace) | Account Console |
| 2 | **Workspace** | Ai được **vào** workspace này, workspace admin, quyền trên object của workspace (notebook, job — khác data) | Workspace Admin → Identity and access |
| 3 | **Metastore** | 1 metastore/region, chứa mọi catalog. Metastore admin quản lý cấp cao nhất của Unity Catalog | (thường 1 cái/account, ít khi động tới) |
| 4 | **Catalog** | `USE CATALOG`, `CREATE SCHEMA`, owner catalog | `GRANT USE CATALOG ON CATALOG x TO ...` |
| 5 | **Schema** | `USE SCHEMA`, `CREATE TABLE`, `SELECT` (áp cho mọi bảng bên trong) | `GRANT SELECT ON SCHEMA x.y TO ...` |
| 6 | **Table/View/Volume/Function** | Quyền trên 1 object cụ thể | `GRANT SELECT ON TABLE x.y.z TO ...` |
| 7 | **Row/Column** | Ẩn dòng, che cột — **có 2 cơ chế khác nhau, xem bên dưới** | Row Filter / Column Mask / ABAC Policy |

**Owner** (người tạo object) luôn có quyền đầy đủ trên object đó ở bất kỳ
tầng nào — GRANT/REVOKE nhắm vào người khác không lấy mất quyền của
owner (xem gotcha thật ở
[roadmap/phase-1-track2-ecommerce-project.md mục 2.7](../../roadmap/phase-1-track2-ecommerce-project.md)).

## Tầng 7 có 2 cơ chế — khác nhau ở loại bảng áp được

### Cơ chế cũ — thủ công, chỉ áp lên TABLE thật

```sql
CREATE FUNCTION cat.schema.my_filter(col STRING) RETURN IS_ACCOUNT_GROUP_MEMBER('admins') OR col != 'x';
ALTER TABLE cat.schema.my_table SET ROW FILTER cat.schema.my_filter ON (col);
```

**Giới hạn thật đã verify**: chỉ áp được lên bảng có `DESCRIBE EXTENDED`
báo `Type = TABLE` hoặc `STREAMING_TABLE`. Áp lên `MATERIALIZED_VIEW` sẽ
fail `EXPECT_TABLE_NOT_VIEW`. Vấn đề: **hầu hết bảng trong 1 Lakeflow
pipeline đều là materialized view** (mọi `@dp.table` đọc batch, không
`readStream`) — xem [Bài 11](11-acid-timetravel-incremental.md). Nên cơ
chế cũ này thực ra chỉ dùng được cho số ít bảng streaming (Bronze fact
table qua Auto Loader), không dùng được cho Silver/Gold.

### Cơ chế mới — ABAC (Attribute-Based Access Control), GA 2026

Áp được lên **cả TABLE lẫn MATERIALIZED VIEW lẫn STREAMING TABLE** — đã tự
verify thật, không phải đọc docs suông. Cách hoạt động: gắn **tag** lên
cột/bảng, viết 1 **policy** áp dụng cho mọi object có tag đó (không cần
`ALTER TABLE` từng bảng một).

```sql
-- 1. Tag có sẵn (hệ thống tự có sẵn ~20 tag PII: class.email_address,
--    class.phone_number, class.us_ssn...) hoặc tự tạo tag riêng:
CREATE GOVERNED TAG sensitivity VALUES ('restricted', 'public');

-- 2. Gắn tag lên cột (dùng tag hệ thống có sẵn hoặc tag vừa tạo)
ALTER TABLE cat.schema.my_table ALTER COLUMN my_col SET TAGS ('sensitivity' = 'restricted');

-- 3. Viết function + policy — áp dụng cho MỌI bảng trong catalog có cột
--    mang tag này, không cần lặp lại ALTER TABLE cho từng bảng
CREATE FUNCTION cat.schema.my_filter(my_col STRING) RETURN IS_ACCOUNT_GROUP_MEMBER('admins') OR my_col != 'x';
CREATE POLICY my_policy
ON CATALOG cat
ROW FILTER cat.schema.my_filter
TO `account users`
FOR TABLES
MATCH COLUMNS has_tag('sensitivity') AS col
USING COLUMNS (col);
```
Column Mask tương tự, dùng `COLUMN MASK <function> ... ON COLUMN col`
thay vì `ROW FILTER`.

⚠️ **Gotcha thật gặp**: tag tự tạo bằng `CREATE GOVERNED TAG` mới xong,
`CREATE POLICY` báo `Unknown tag policy key` ngay lập tức — hóa ra chỉ là
**delay đồng bộ** vài chục giây/phút giữa lúc tạo tag và lúc policy engine
nhận ra. Thử lại sau vài phút thì chạy OK. Nếu gặp lỗi này, đừng vội kết
luận "không hỗ trợ" — đợi rồi thử lại trước.

## Áp dụng vào project — đã build + verify thật cả 2 cơ chế

| Bảng | Loại | Cơ chế dùng | Kết quả verify |
|---|---|---|---|
| `bronze_order_items` | `STREAMING_TABLE` | Cơ chế cũ (`ALTER TABLE SET ROW FILTER`/`SET MASK`) | 183,378 → 82,390 dòng (Row Filter), `customer_id` → `***MASKED***` (Column Mask) |
| `bronze_customers` | `MATERIALIZED_VIEW` | **ABAC** (`CREATE POLICY` + tag `class.phone_number`) | `phone` → `***` |
| `gold_daily_category_revenue` | `MATERIALIZED_VIEW` | **ABAC** (`CREATE POLICY` + tag `sensitivity`) | 8 category → còn 7 (mất `Electronics`) |

## Cách test bằng identity thật, độc lập — không cần mượn tài khoản ai

Test bằng chính bạn (không phải admin) chỉ verify được 1 nửa — GRANT/
REVOKE không tác dụng lên **owner** (chính bạn, nếu bạn tạo ra catalog).
Cách test đúng, độc lập hoàn toàn — dùng **Service Principal** (không cần
email thật thứ 2):

```powershell
# 1. Tạo service principal
databricks service-principals create --display-name "test-non-admin-sp" --profile DEFAULT

# 2. Sinh OAuth secret cho nó (dùng <id> từ bước 1)
databricks service-principal-secrets-proxy create <id> --profile DEFAULT

# 3. Thêm profile mới vào ~/.databrickscfg (dùng client_id + secret vừa sinh,
#    KHÔNG commit secret vào git)
[test_sp]
host = https://<workspace>
client_id = <application_id>
client_secret = <secret>
```
```python
# 4. Query bằng identity này — set biến môi trường trước khi chạy
# DATABRICKS_CONFIG_PROFILE=test_sp uv run python -c "..."
from databricks.connect import DatabricksSession
spark = DatabricksSession.builder.serverless(True).getOrCreate()
spark.sql("SELECT current_user()").show()  # xác nhận đúng là SP, không phải bạn
```

**Đã verify thật bằng service principal** (không phải mình tự suy diễn):
- Query `gold_daily_category_revenue` → đúng 7/8 category (Row Filter hoạt động thật với identity không phải owner)
- Query `bronze_customers` → `INSUFFICIENT_PERMISSIONS` trên schema `bronze` (REVOKE hoạt động thật, không bị owner-bypass như lúc test bằng chính mình)

Cách này áp dụng y hệt cho cả 2 kiểu tổ chức catalog: 1 catalog/3 schema
layer (chỉ đổi path `cat.schema.table`) hay 3 catalog dev/staging/prod
(chạy lại full script cho từng catalog) — cơ chế GRANT/Policy không đổi,
chỉ đổi object đích.

## Đọc thêm
- [Manage privileges in Unity Catalog](https://docs.databricks.com/aws/en/data-governance/unity-catalog/manage-privileges/)
- [Attribute-based access control (ABAC)](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/core-concepts)
- [Governed tags](https://docs.databricks.com/aws/en/admin/governed-tags/)
