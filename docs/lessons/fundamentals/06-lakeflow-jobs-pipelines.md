# Bài 6 — Lakeflow Jobs / Pipelines

## Mục tiêu
Hiểu Lakeflow là gì và cách orchestrate nhiều task thành 1 pipeline có
dependency, giống các công cụ orchestration khác bạn có thể đã biết.

## Nội dung

Tên hiện tại nên biết là **Lakeflow** — Databricks gom data engineering
quanh Lakeflow, gồm ingestion, pipelines, và orchestration (Lakeflow Jobs).

### Ví dụ workflow

```
Task 1: Ingest data
   ↓
Task 2: Clean data
   ↓
Task 3: Build Gold tables
   ↓
Task 4: Refresh BI
```

Lakeflow Jobs dùng để schedule/orchestrate các task, hỗ trợ dependency,
branching, looping. Ví dụ:

```
Daily at 02:00

ingest_orders
      ↓
clean_orders
      ↓
aggregate_sales
      ↓
refresh_dashboard
```

Nếu từng dùng **Airflow DAG**, **AWS Step Functions**, hay
**Azure Data Factory Pipeline** — ý tưởng khá tương tự (task, dependency,
schedule, retry).

## Áp dụng vào project

- [resources/sample_job.job.yml](../../../resources/sample_job.job.yml) —
  job thật với 3 task (`notebook_task` → `python_wheel_task` +
  `refresh_pipeline`), có `depends_on`, `trigger.periodic`.
- [resources/my_project_etl.pipeline.yml](../../../resources/my_project_etl.pipeline.yml) —
  Lakeflow declarative pipeline (khai báo transformation bằng `@dp.table`,
  không cần tự viết orchestration bên trong pipeline).
- Bài tập nối chuỗi task thật: xem
  [roadmap/phase-1-track1-cdc-demo.md mục 1.8](../../roadmap/phase-1-track1-cdc-demo.md).
