# Bài 2 — Databricks Free Edition: giới hạn

## Mục tiêu
Biết chính xác bản Free đang dùng thiếu gì so với bản trả phí, để không bị
bất ngờ khi 1 tính năng "không hoạt động" — và biết khi nào bắt buộc phải
lên Premium (Phase 2 của [roadmap](../../roadmap/OVERVIEW.md)).

## Nội dung

Free Edition thay thế Community Edition (đã retired 2025), chạy trên nền
serverless hiện đại. Nguồn: tài liệu chính thức Databricks AWS —
[Free Edition limitations](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations).

### Compute
- Chỉ dùng được **serverless compute** — không tạo được cluster tùy chỉnh, không GPU.
- SQL warehouse: chỉ **1 cái**, giới hạn size **2X-Small**.
- Job: tối đa **5 concurrent job tasks** / account.
- Lakeflow pipeline: **1 pipeline đang active / loại pipeline**.
- Outbound internet: chỉ tới domain được whitelist sẵn (mở rộng được nếu verify bằng LinkedIn).

### Model Serving & AI
- Giới hạn số serving endpoint đang active, **không có GPU serving endpoint**.
- Không có provisioned throughput / custom GPU model, 1 số model không dùng được.
- 1 AI Search endpoint, giới hạn 1 search unit; không hỗ trợ Direct Vector Access.

### Apps & Projects
- Tối đa **3 Databricks Apps** / account, app tự dừng sau **24h**.
- **1 Lakebase project** / account (scale-to-zero).

### Account & Auth
- **1 workspace + 1 metastore / account** (không tạo thêm workspace được).
- Không có account console / account-level API.
- Đăng nhập chỉ qua **email OTP, Google, Microsoft** — không SSO/SCIM.
- Không có private networking, không compliance enforcement.

### Không hỗ trợ
R, Scala, **custom workspace storage** (⇒ không tạo Storage Credential/
External Location thật), online tables, clean rooms, 1 số tính năng legacy,
Knowledge Assistant.

### Khác
- Không SLA, không nằm trong support policy chính thức.
- Chỉ dùng **phi thương mại**, không được làm Marketplace provider.
- Account không hoạt động lâu ngày có thể bị xóa.
- Có **fair usage policy**: vượt quota → compute bị tắt hết ngày đó (nặng
  thì cả tháng).

## ⚠️ Đã sửa 1 hiểu nhầm quan trọng (verify thật trên workspace, không phải đoán)

Ban đầu tài liệu này ghi "Free Edition chỉ có 1 catalog `workspace`, phải
đợi Premium mới tạo thêm catalog được" — **sai**. Đã tự tay verify bằng
`CREATE CATALOG`, `GRANT`, `CREATE FUNCTION ... SET ROW FILTER`,
`SET MASK` trên chính workspace Free Edition đang dùng — **tất cả chạy
được**, không cần Premium:

```sql
CREATE CATALOG my_new_catalog;          -- OK, dùng default managed storage
GRANT SELECT ON CATALOG my_new_catalog TO `account users`;  -- OK
-- CREATE FUNCTION ... SET ROW FILTER ...  -- OK
-- ALTER TABLE ... SET MASK ...            -- OK
```

**Giới hạn thật, hẹp hơn nhiều so với tôi từng nói:** "1 workspace + 1
metastore / account" (đúng, xem trên) ≠ "1 catalog" — 1 metastore chứa
được **nhiều catalog**. Cái Free Edition thật sự chặn là dòng "custom
workspace storage" — nghĩa là **không tự mang storage thật của mình** (tạo
Storage Credential trỏ vào Azure Access Connector/AWS IAM role riêng, để
gắn 1 bucket ADLS/S3 có sẵn ngoài đời) — không phải "không tạo được
catalog". Catalog mới tạo bằng `CREATE CATALOG` mặc định dùng **default
managed storage** của chính Free Edition, không cần Storage Credential.

## Áp dụng vào project

- 1 workspace duy nhất → không làm được pattern "3 workspace theo 3 môi
  trường" (xem [Bài 4 — Unity Catalog](../fundamentals/04-unity-catalog.md)) —
  **nhưng pattern catalog-per-environment (nhiều catalog) vẫn làm được
  ngay trên Free Edition**, chỉ cần dùng default storage.
- "Không custom workspace storage" chỉ chặn đúng 1 việc: gắn ADLS Gen2/S3
  **thật, thuộc sở hữu của bạn**. Đây là lý do duy nhất còn lại khiến
  **Phase 2** (Storage Credential, External Location trỏ vào cloud storage
  thật) phải đợi Premium trial — mọi phần Unity Catalog governance khác
  (catalog, GRANT/REVOKE, Row Filter, Column Mask) đã dời sang Phase 1.
- Lakeflow pipeline vẫn dùng được đầy đủ (kể cả Auto Loader, AUTO CDC/SCD2)
  trên Free Edition — chỉ giới hạn 1 pipeline active/loại, không phải bị
  chặn tính năng.

## Đọc thêm
- [Free Edition limitations (AWS)](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations)
- [Resource limits (bản trả phí, để so sánh)](https://docs.databricks.com/aws/en/resources/limits)
