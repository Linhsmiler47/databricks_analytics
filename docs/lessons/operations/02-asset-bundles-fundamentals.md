# Bài 3 — Databricks Asset Bundles (DAB): deploy-time vs run-time

## Mục tiêu
Hiểu chính xác bundle quản lý gì, không quản lý gì — và tại sao `deploy`
không có nghĩa là "chạy".

## Nội dung

**Databricks Asset Bundle = IaC cho code + resource definitions** (job,
pipeline, notebook, permissions) — **không quản lý data**. Data sống trong
Unity Catalog (`catalog.schema.table`), tách biệt hoàn toàn khỏi git/bundle.

### Deploy-time vs run-time — 2 thời điểm khác nhau

| | `databricks bundle deploy` | Job/pipeline chạy |
|---|---|---|
| Xảy ra khi nào | Bạn/CI chủ động chạy | Theo lịch, trigger, hoặc bấm run |
| Làm gì | Upload code, tạo/update job+pipeline definition | Thực thi code đó |
| Tự detect data mới? | **Không** — chỉ "cài đặt" | **Có** — nếu code dùng Auto Loader/CDF |

Auto Loader không phải tính năng của bundle — nó là code Python bạn viết,
nằm trong file transformation. Bundle chỉ đưa đúng file đó lên đúng
workspace; việc detect file mới là Spark runtime làm lúc pipeline **chạy**,
không liên quan gì tới việc bạn deploy bằng bundle hay bằng tay qua UI.

### `mode: development` vs `mode: production`

Trong `databricks.yml`, mỗi target khai báo 1 mode:
- `development`: resource được prefix `[dev <username>]`, **schedule tự
  động bị pause** — an toàn để thử nghiệm.
- `production`: tên resource giữ nguyên, schedule chạy thật theo trigger
  khai báo (vd `periodic: 1 DAYS`).

### Giá trị thật của bundle (không phải "làm data tự chạy")

1. Version control — mọi thay đổi logic nằm trong git, có history, review qua PR.
2. Tái tạo môi trường giống hệt nhau — nhiều target từ 1 nguồn code.
3. CI/CD — tự động deploy khi merge, không ai tay chân click UI production.
4. Review trước khi chạy production — PR thay vì sửa trực tiếp UI.
5. Đồng bộ nhiều resource cùng lúc — 1 lệnh deploy cả job + pipeline + permissions.

## Áp dụng vào project

- [databricks.yml](../../../databricks.yml) — 3 target `dev`/`staging`/`prod`.
- [resources/sample_job.job.yml](../../../resources/sample_job.job.yml) — job
  định nghĩa, `trigger.periodic` bị pause ở dev.
- Thực tế đã gặp: `bundle deploy` chạy xong nhưng job "chưa chạy lần nào"
  cho tới khi gõ `bundle run` — đúng minh chứng deploy-time ≠ run-time.

## Đọc thêm
- [Databricks Asset Bundles — docs](https://docs.databricks.com/dev-tools/bundles/index.html)
- [Deployment modes](https://docs.databricks.com/dev-tools/bundles/deployment-modes.html)
