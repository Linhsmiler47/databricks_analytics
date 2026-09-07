# Docs — mục lục

| File / Folder | Dùng khi nào |
|---|---|
| [architecture.md](architecture.md) | Kiến trúc hiện tại của repo: job, pipeline, data flow, environments — có ghi chú theo từng phase. |
| [dev-workflow.md](dev-workflow.md) | Vòng lặp phát triển hằng ngày: `uv sync` → test → validate → deploy → run. Lặp lại nhiều lần. |
| [lessons/](lessons/INDEX.md) | **Học khái niệm**, không phải việc cần làm. 2 nhóm: [fundamentals/](lessons/fundamentals) (Spark, Delta Lake, Unity Catalog, Lakeflow... — kiến thức Databricks tổng quát) và [operations/](lessons/operations) (Free Edition, Asset Bundles, CI/CD, Git Folder — cách project này vận hành). |
| [roadmap/OVERVIEW.md](roadmap/OVERVIEW.md) | **Planning cấp cao**: đang ở phase/track nào, vì sao chia vậy — không có lệnh kỹ thuật. |
| [roadmap/phase-1-track1-cdc-demo.md](roadmap/phase-1-track1-cdc-demo.md) | **Track 1** — CDC/SCD2 (`customers`, data nhỏ tự edit tay), từ setup (1.1) tới AUTO CDC, có tickbox. |
| [roadmap/phase-1-track2-ecommerce-project.md](roadmap/phase-1-track2-ecommerce-project.md) | **Track 2** — E-commerce (data thật, catalog-per-env) — đã build + deploy + chạy thật, kèm 7 lỗi data đã fix. |
| [roadmap/phase-2-trial-security.md](roadmap/phase-2-trial-security.md) | **Phase 2** — chỉ còn phần storage thật (ADLS/S3), phần Unity Catalog governance đã dời sang Phase 1 Track 2. |

**Quy tắc phân biệt nhanh:**
- **lessons** = hiểu khái niệm (không đổi theo thời gian nhiều, đọc lại khi quên).
- **roadmap/OVERVIEW** = đang ở đâu, tại sao (planning, không có lệnh).
- **roadmap/phase-N** = làm gì, chạy lệnh gì, tickbox tiến độ (đổi liên tục, tự chứa để chạy lại từ đầu).
- **dev-workflow** = vòng lặp sửa-code-hằng-ngày, khác với setup 1 lần trong phase-1 mục 1.1.
