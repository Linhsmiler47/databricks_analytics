# Databricks — Lessons (học từ đầu)

Đây là "giáo trình" khái niệm — **học để hiểu, không phải để làm**. Khác
với [../roadmap/](../roadmap/OVERVIEW.md) (kế hoạch **làm gì tiếp theo** +
tickbox tiến độ trên chính project này), folder này chỉ có kiến thức, đọc
lại bất cứ lúc nào khi quên.

Chia 2 nhóm rõ ràng — đừng lẫn:

## Phần A — Nền tảng Data Engineering ([fundamentals/](fundamentals/))

Kiến thức Databricks **tổng quát**, đúng ở bất kỳ project nào, cần cho cả
phỏng vấn lẫn công việc thật. Học theo thứ tự:

1. [Lakehouse & Medallion Architecture](fundamentals/01-lakehouse-and-medallion.md)
2. [Apache Spark cơ bản](fundamentals/02-spark-fundamentals.md)
3. [Delta Lake](fundamentals/03-delta-lake.md)
4. [Unity Catalog](fundamentals/04-unity-catalog.md)
5. [Compute](fundamentals/05-compute.md)
6. [Lakeflow Jobs / Pipelines](fundamentals/06-lakeflow-jobs-pipelines.md)
7. [SQL + PySpark](fundamentals/07-sql-and-pyspark.md)
8. [Performance & Partitioning](fundamentals/08-performance-and-partitioning.md)
9. [Ôn phỏng vấn & lộ trình cấp tốc](fundamentals/09-interview-prep-and-crash-course.md)
10. [Volume & Auto Loader: từ file thô tới Delta table](fundamentals/10-volumes-and-autoloader.md)
11. [ACID, Time Travel, Incremental: áp dụng vào layer nào](fundamentals/11-acid-timetravel-incremental.md)
12. [Phân quyền từ cao xuống thấp: hierarchy + ABAC](fundamentals/12-permissions-hierarchy-and-abac.md)
13. [Delta Table + Job vs Lakeflow (Streaming Table/Materialized View)](fundamentals/13-delta-table-job-vs-lakeflow.md)

## Phần B — Vận hành Databricks Asset Bundles ([operations/](operations/))

Kiến thức **riêng cho cách project này vận hành** (DAB, CI/CD, tooling) —
không phải Databricks nói chung, mà là cách dùng Databricks qua bundle/CLI.

1. [Free Edition — giới hạn](operations/01-free-edition-limitations.md)
2. [Asset Bundles: deploy-time vs run-time](operations/02-asset-bundles-fundamentals.md)
3. [CI/CD với bundle](operations/03-cicd-with-bundles.md)
4. [Git Folder vs Bundle deploy](operations/04-git-folder-vs-bundle-deploy.md)
5. [Gotchas thực chiến](operations/05-gotchas-thuc-chien.md)

---

Mỗi bài có mục **Áp dụng vào project** trỏ tới đúng file/dòng trong repo
minh họa khái niệm đó — đọc xong nên mở file thật ra đối chiếu.
