# Phase 2 — Storage thật trên Premium trial

⚠️ **Đã thu hẹp phạm vi so với bản trước.** Từng nghĩ toàn bộ Unity Catalog
(nhiều catalog, GRANT/REVOKE, Row Filter, Column Mask, audit/lineage) đều
cần Premium — **sai**, đã verify thật trên Free Edition, tất cả chạy được
(xem [lessons/operations/01-free-edition-limitations.md](../lessons/operations/01-free-edition-limitations.md)).
Toàn bộ phần đó giờ nằm trong **Phase 1** (mục e-commerce project, catalog
`ecomm_dev`/`ecomm_staging`/`ecomm_prod`).

**Phase 2 giờ chỉ còn đúng 1 việc**: gắn Databricks vào cloud storage
**thật, thuộc sở hữu của bạn** (ADLS Gen2/S3) thay vì dùng default managed
storage — đây là giới hạn duy nhất Free Edition thật sự có ("custom
workspace storage" unsupported).

⚠️ Đọc phần **Cảnh báo chi phí** ở [OVERVIEW.md](OVERVIEW.md) trước khi bắt
đầu — storage thật + Azure/AWS subscription là nơi dễ bị tính phí ngoài ý
muốn nhất trong toàn bộ roadmap.

## Tickbox tiến độ

- [ ] 2.0 — Chuẩn bị tài khoản Azure/AWS trial + budget alert
- [ ] 2.1 — Tạo Storage Account (ADLS Gen2) + Access Connector
- [ ] 2.2 — Tạo Storage Credential + External Location trong Databricks
- [ ] 2.3 — Tạo 1 catalog demo dùng `MANAGED LOCATION` trỏ storage thật, verify file thật xuất hiện trên Azure Portal
- [ ] Dọn dẹp trước khi hết trial

## 🔧 Cheat sheet lệnh

| Bước | Lệnh / thao tác chính |
|---|---|
| 2.0 | Tạo Azure/AWS account mới, bật budget alert |
| 2.1 | Azure Portal: tạo Storage Account (hierarchical namespace bật) + Access Connector for Databricks |
| 2.2 | Catalog Explorer → Create Credential (trỏ Access Connector) → Create External Location (trỏ container) |
| 2.3 | `CREATE CATALOG demo_real_storage MANAGED LOCATION 'abfss://...'` → `CREATE TABLE ...` → xem file trên Azure Portal |
| Dọn dẹp | Xóa catalog → External Location → Storage Credential → Storage Account → hủy subscription |

## 2.0 — Chuẩn bị tài khoản

- Tạo Azure account mới (hoặc AWS) để kích hoạt trial — không dùng chung
  account Free Edition đang có, tránh lẫn lộn billing.
- Xác nhận role: cần **Account Admin** trên Databricks account console để
  tạo storage credential.
- Trên Azure/AWS: cần quyền tạo **Storage Account** và **Access
  Connector/IAM role** — nếu dùng account công ty có thể bị chặn bởi
  policy, nên dùng account cá nhân cho trial này.
- Bật budget alert (Azure Cost Management/AWS Budgets) ngưỡng thấp ngay
  khi có subscription.

## 2.1 — Storage Account + Access Connector (phía Azure)

1. Tạo Storage Account (ADLS Gen2, bật hierarchical namespace).
2. Tạo 1 container, vd `demo-container`.
3. Tạo **Access Connector for Databricks** (managed identity).
4. Gán role `Storage Blob Data Contributor` cho Access Connector đó trên
   Storage Account.

## 2.2 — Storage Credential + External Location (phía Databricks)

Catalog Explorer → External Data:
1. **Create Credential** → trỏ tới Access Connector ở bước 2.1.
2. **Create External Location** → trỏ `abfss://demo-container@<storage_account>.dfs.core.windows.net/`, dùng credential vừa tạo.

**Tiêu chí xong:** External Location hiện "Path exists" khi Databricks
test connection.

## 2.3 — Tạo catalog dùng storage thật

```sql
CREATE CATALOG demo_real_storage
MANAGED LOCATION 'abfss://demo-container@<storage_account>.dfs.core.windows.net/';

CREATE SCHEMA demo_real_storage.test;
CREATE TABLE demo_real_storage.test.hello AS SELECT 1 AS id;
```

**Tiêu chí xong:** vào Azure Portal → Storage Account → container →
thấy thư mục `test/hello/_delta_log/` xuất hiện thật — khác với mọi
catalog ở Phase 1 (dùng default managed storage, file nằm trong hạ tầng
nội bộ Databricks quản lý, bạn không tự thấy được).

**Không cần "promote" `ecomm_dev/staging/prod`** sang catalog này — 3
catalog đó ở Phase 1 vẫn hoạt động bình thường với default storage, không
có lý do kỹ thuật nào bắt buộc phải đổi. Bài tập 2.3 chỉ để **thấy** sự
khác biệt giữa 2 loại storage, không phải để migrate project thật.

## Kết thúc Phase 2 — dọn dẹp (bắt buộc)

1. Backup ghi chú/kết quả (ảnh chụp Azure Portal, code) trước khi xóa.
2. Xóa catalog `demo_real_storage` → External Location → Storage
   Credential (đúng thứ tự phụ thuộc).
3. Xóa Storage Account trên Azure Portal (nơi tốn phí âm thầm nhất nếu quên).
4. Hủy/downgrade subscription trial trước ngày hết hạn.
