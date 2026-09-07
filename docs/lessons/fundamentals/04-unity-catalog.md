# Bài 4 — Unity Catalog

## Mục tiêu
Thuộc lòng namespace 3 cấp + vị trí của nó trong hierarchy toàn hệ thống,
và biết 3 tầng có thể dùng để tách môi trường (dev/staging/prod).

## Nội dung

Unity Catalog là **governance layer** của Databricks — quản lý quyền truy
cập, lineage, auditing và discovery cho data/AI assets.

### Namespace 3 cấp

```
catalog.schema.table
```

Ví dụ: `production.sales.orders`
- `production` = catalog
- `sales` = schema
- `orders` = table

```sql
SELECT * FROM production.sales.orders;

GRANT SELECT
ON TABLE production.sales.orders
TO `data_analysts`;
```

### Databricks hierarchy đầy đủ (nên nhớ khi phỏng vấn)

```
Account
   ↓
Workspace
   ↓
Unity Catalog Metastore
   ↓
Catalog
   ↓
Schema
   ↓
Table / View / Volume / Function
```

**Thuật ngữ nên biết:** Catalog, Schema, Table, Volume, Permissions,
Lineage.

### Tách môi trường (dev/staging/prod) có thể xảy ra ở 3 TẦNG khác nhau

Đây là điểm hay gây nhầm nhất: "1 catalog, 3 schema bronze/silver/gold" và
"3 catalog dev/staging/prod" **không phải 2 pattern đối lập** — chúng trả
lời 2 câu hỏi khác nhau, có thể kết hợp:
- **Câu hỏi 1**: môi trường (dev/staging/prod) tách ở đâu?
- **Câu hỏi 2**: layer (Bronze/Silver/Gold) tổ chức thế nào?

Câu hỏi 2 hầu như luôn trả lời bằng **schema** (mỗi layer 1 schema, hoặc
gộp 1 schema + đặt tên prefix `bronze_`/`silver_`/`gold_`). Câu hỏi 1 mới
là chỗ có nhiều lựa chọn — tách ở **3 tầng** khác nhau trong hierarchy:

| Tách môi trường ở tầng | Cấu trúc |
|---|---|
| **Workspace** (mỗi env 1 workspace riêng) | Mỗi workspace: 1 catalog (vd đặt theo tên project) → 3 schema layer bên trong |
| **Catalog** (1 workspace, nhiều catalog) | `dev_catalog`/`staging_catalog`/`prod_catalog`, mỗi catalog → 3 schema layer bên trong |
| **Schema** (1 workspace, 1 catalog) | 1 catalog → schema đặt theo tên môi trường (`dev`/`staging`/`prod`), không tách layer bằng schema nữa (dùng prefix tên bảng) |

**Doanh nghiệp thật thường tách ở tầng Workspace** — mỗi môi trường 1
workspace riêng (network, compute, quyền truy cập tách biệt hoàn toàn).
Bên trong mỗi workspace, catalog thường đặt theo **tên project/domain**,
không phải tên môi trường — vì môi trường đã được workspace lo rồi, catalog
chỉ cần lo phân lớp Bronze/Silver/Gold. Đây là lý do 1 kỹ sư maintain trong
1 workspace "prod" của khách hàng thường chỉ thấy **1 catalog, 3 schema
layer** — không phải vì họ không tách môi trường, mà vì môi trường được
tách ở tầng workspace, nằm ngoài tầm nhìn của người chỉ có quyền vào 1
workspace.

⚠️ **Đính chính**: trước đây bài này ghi "Catalog-per-env cần Premium, Free
Edition chỉ làm được Schema-per-env" — **sai**, đã tự tay verify bằng
`CREATE CATALOG` thật trên Free Edition, chạy OK (dùng default managed
storage, không cần Storage Credential). Free Edition làm được cả
catalog-per-env lẫn schema-per-env — chỉ riêng **workspace-per-env** là
thật sự không làm được (Free Edition giới hạn 1 workspace/account).

## Áp dụng vào project

Demo `nyctaxi` (có sẵn từ template) tách ở **tầng schema** — xem
[databricks.yml](../../../databricks.yml): cả 3 target (`dev`/`staging`/
`prod`) đều `catalog: workspace`, chỉ khác `schema`. Đây là lựa chọn vì
đơn giản, không phải giới hạn kỹ thuật.

Project e-commerce (`fixtures/ecomm_raw/`, project chính) tách ở **tầng
catalog** — `ecomm_dev`/`ecomm_staging`/`ecomm_prod`, mỗi catalog có 3
schema `bronze`/`silver`/`gold` bên trong, xem
[roadmap/phase-1-ecommerce.md](../../roadmap/phase-1-ecommerce.md).
**Nếu chỉ nhìn riêng 1 catalog** (vd `ecomm_dev`) — đây chính xác là cấu
trúc "1 catalog, 3 schema layer" thường gặp khi maintain 1 workspace prod
có sẵn (tách ở tầng workspace, không tách ở tầng catalog nữa).

Phase 2 giờ chỉ còn đúng 1 việc Free Edition thật sự không làm được: gắn
storage thật của bạn (ADLS Gen2/S3) — xem
[operations/01-free-edition-limitations.md](../operations/01-free-edition-limitations.md).

## Đọc thêm
- [Unity Catalog overview — Databricks docs](https://docs.databricks.com/aws/en/data-governance/unity-catalog/)
