# Roadmap — Overview (high-level, không có lệnh kỹ thuật)

Kế hoạch học Databricks chia 2 giai đoạn. Mọi câu lệnh, code mẫu, tickbox
chi tiết nằm trong file phase tương ứng — file này chỉ trả lời **đang ở
đâu** và **tại sao chia như vậy**.

## ⚠️ Đã sửa 1 hiểu nhầm quan trọng (2026)

Ban đầu roadmap này giả định **toàn bộ Unity Catalog governance** (nhiều
catalog, GRANT/REVOKE, Row Filter, Column Mask) cần Premium — **sai**, đã
verify thật bằng CLI/SQL trên Free Edition, tất cả chạy được. Giới hạn
thật duy nhất: **không tự mang cloud storage của bạn** (ADLS Gen2/S3 thật).
Đã cập nhật lại toàn bộ split bên dưới. Chi tiết:
[lessons/operations/01-free-edition-limitations.md](../lessons/operations/01-free-edition-limitations.md).

## Trạng thái hiện tại

| Phase | Trạng thái | Chi tiết |
|---|---|---|
| **Phase 1 · Track 1** — CDC/SCD2 (`customers`) | 🟡 Đang làm | [phase-1-track1-cdc-demo.md](phase-1-track1-cdc-demo.md) |
| **Phase 1 · Track 2** — E-commerce (catalog-per-env) | 🟢 Bronze/Silver/Gold đã deploy + chạy thật thành công | [phase-1-track2-ecommerce-project.md](phase-1-track2-ecommerce-project.md) |
| **Phase 2** — Storage thật | ⚪ Chưa bắt đầu | [phase-2-trial-security.md](phase-2-trial-security.md) |

Vòng lặp sửa code hằng ngày (không phải kế hoạch, mà là quy trình lặp lại
mỗi khi code thay đổi): [dev-workflow.md](../dev-workflow.md).

## Phase 1 — Free Edition (~90% thời gian) — 2 track song song

1. **Track 1 — CDC/SCD2** (`fixtures/cdc_demo/`) — case study nhỏ, tự tay
   edit CSV, luyện Bronze/Silver/Gold + Auto Loader + AUTO CDC + SCD Type 2.
2. **Track 2 — E-commerce** (`fixtures/ecomm_raw/`) — dataset thật (star
   schema: brands/category/date/products/customers/order_items, 183K dòng
   order_items thật), dùng **catalog-per-environment**
   (`ecomm_dev`/`ecomm_staging`/`ecomm_prod`) + GRANT/REVOKE + Row Filter +
   Column Mask — **tất cả làm được trên Free Edition**, không cần đợi
   Phase 2. Bronze/Silver/Gold đã build, deploy, chạy thật thành công —
   kèm 7 lỗi data thật đã tìm và fix (xem
   [phase-1-track2-ecommerce-project.md](phase-1-track2-ecommerce-project.md)).

Cả 2 track dùng chung kỹ năng nền: PySpark, Medallion, parameterization,
data quality, orchestration, testing.

## Phase 2 — Storage thật (Premium trial 14 ngày, ~10% thời gian)

Thu hẹp lại còn đúng 1 việc: gắn Databricks vào cloud storage **thật,
thuộc sở hữu của bạn** (ADLS Gen2/S3) thay vì default managed storage —
đây là giới hạn duy nhất Free Edition thật sự có
("custom workspace storage" unsupported). Không cần "promote" lại
`ecomm_dev/staging/prod` — 3 catalog đó dùng default storage vẫn hoạt
động bình thường, bài tập Phase 2 chỉ để thấy sự khác biệt.

## ⚠️ Cảnh báo chi phí (đọc trước khi bắt đầu Phase 2)

Trial Premium/Enterprise thường 14 ngày miễn phí rồi **tự động tính phí
thật**. Việc cần làm ngay khi bắt đầu Phase 2:
1. Ghi ngày hết hạn vào lịch, đặt reminder trước 2 ngày.
2. Bật budget alert (Azure/AWS) ngưỡng thấp ngay khi tạo tài khoản.
3. Trước hạn: xóa Storage Account trước (tốn phí âm thầm nhất) → catalog → subscription.
4. Backup code/docs/ghi chú trước khi xóa — data trong catalog trial sẽ mất.

## Tài liệu khác
- [../lessons/INDEX.md](../lessons/INDEX.md) — học khái niệm (Spark, Delta Lake, Unity Catalog...).
- [../architecture.md](../architecture.md) — kiến trúc hiện tại + theo từng phase.
