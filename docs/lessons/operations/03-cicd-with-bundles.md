# Bài 4 — CI/CD với Asset Bundles

## Mục tiêu
Biết cách ghép bundle vào CI/CD thật, và phân biệt 2 trục cách ly môi
trường độc lập nhau: workspace vs catalog.

## Nội dung

### 2 trục cách ly độc lập

| | Workspace riêng / môi trường | Workspace chung, catalog/schema riêng |
|---|---|---|
| Cách ly gì | Network, compute, IAM, cost tracking | Chỉ data + permissions (metastore dùng chung) |
| Chi phí vận hành | Cao — quản nhiều workspace | Thấp — 1 workspace |
| Khi nào dùng | Doanh nghiệp lớn, compliance | Team nhỏ/vừa, learning, Free Edition |

3 pattern thực tế: (A) 3 workspace riêng + catalog cùng tên mỗi workspace —
cách ly mạnh nhất, tốn kém; (B) 1 workspace, 3 catalog — hướng Unity
Catalog hiện đại đang khuyến khích; (C) 2 workspace (non-prod + prod),
catalog tách trong non-prod — dung hòa.

### CI/CD flow điển hình

Mỗi **target** trong `databricks.yml` = 1 environment. CI/CD chỉ là:
trigger đúng lệnh `bundle deploy --target <env>` đúng lúc, dùng **service
principal** (không phải tài khoản cá nhân) để deploy production.

```
PR mở                  → CI: bundle validate + pytest (không deploy)
Merge vào main          → CI: bundle deploy --target dev   (tự động)
Tag / approve thủ công  → CI: bundle deploy --target prod  (cần review)
```

Điểm khác với deploy tay:
- Target `prod` nên có `run_as:` trỏ service principal, không phải email cá nhân.
- Credentials CI (client-id/secret) lưu ở GitHub Secrets, không commit vào repo.
- Nếu dùng pattern A/C (nhiều workspace): mỗi target 1 `workspace.host` khác nhau.
  Nếu pattern B (1 workspace): cùng host, chỉ khác `variables.catalog`/`schema`
  — đúng như repo này đang làm.

## Áp dụng vào project

Repo hiện dùng pattern B thu gọn (bắt buộc do Free Edition — xem
[Bài 1](01-free-edition-limitations.md)): cả 3 target cùng
`https://dbc-4c2ccca6-b3b8.cloud.databricks.com`, khác `catalog`/`schema`.
CI/CD thật cho repo này còn nằm trong TODO — xem
[roadmap](../../roadmap/OVERVIEW.md).

## Đọc thêm
- [CI/CD with Databricks Asset Bundles](https://docs.databricks.com/dev-tools/bundles/ci-cd.html)
