# Architecture

## Tổng quan

Bundle này (`my_project`, Databricks Asset Bundle) gồm 1 job + 1 declarative
pipeline, xử lý data mẫu NYC Taxi có sẵn trong mọi workspace Databricks
(catalog `samples`, không phải data tự import).

```
                      ┌─────────────────────────────┐
                      │  samples.nyctaxi.trips       │  ← dataset mẫu có sẵn
                      │  (catalog "samples", chỉ đọc) │     trong mọi workspace
                      └───────────────┬──────────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              │ dùng bởi                                       │ dùng bởi
              ▼                                                 ▼
┌───────────────────────────┐                  ┌───────────────────────────────┐
│ src/my_project/taxis.py    │                  │ Pipeline: my_project_etl        │
│  find_all_taxis()           │                  │ (resources/my_project_etl.pipeline.yml)
│                             │                  └───────────────┬────────────────┘
│ dùng bởi:                   │                                   │
│  - main.py (wheel task)     │                  ┌────────────────▼────────────────┐
│  - tests/sample_taxis_test.py│                 │ Table: sample_trips_my_project    │
└───────────────────────────┘                  │  = spark.read.table(nyctaxi.trips)│
                                                  └────────────────┬────────────────┘
                                                                   │ group by pickup_zip,
                                                                   │ sum(fare_amount)
                                                  ┌────────────────▼────────────────┐
                                                  │ Table: sample_zones_my_project    │
                                                  └────────────────────────────────┘
```

## Job: `sample_job`

Định nghĩa: [resources/sample_job.job.yml](../resources/sample_job.job.yml)

```
notebook_task (sample_notebook.ipynb)
        │
        ├──► python_wheel_task (my_project.main:main)  — show() 5 dòng taxis
        │
        └──► refresh_pipeline  (chạy pipeline my_project_etl)
```

- Trigger: `periodic`, mỗi 1 ngày. **Bị pause tự động** khi deploy target `dev`
  (do `mode: development`); chạy thật ở target `prod`.
- Nhận tham số `catalog`/`schema` từ biến bundle (`var.catalog`, `var.schema`).

## Pipeline: `my_project_etl` (Lakeflow declarative pipeline)

Định nghĩa: [resources/my_project_etl.pipeline.yml](../resources/my_project_etl.pipeline.yml)
Code: [src/my_project_etl/transformations/](../src/my_project_etl/transformations/)

- Serverless, chạy trong `${var.catalog}.${var.schema}`.
- 2 table (Lakeflow `@dp.table`):
  1. `sample_trips_my_project` — copy nguyên `samples.nyctaxi.trips`.
  2. `sample_zones_my_project` — tổng `fare_amount` theo `pickup_zip`, đọc từ
     table (1) ở trên (không đọc lại từ `samples` — đây là ví dụ transform
     nhiều tầng trong 1 pipeline).

## Environments (xem thêm quyết định ở phần chat/README)

| Target | Catalog | Schema | Ghi chú |
|---|---|---|---|
| `dev` | `workspace` | `${workspace.current_user.short_name}` (vd `mychivodoi123`) | mỗi dev có schema riêng, schedule bị pause |
| `staging` | `workspace` | `staging` | `mode: production` (không prefix, không pause), dùng chung không theo user |
| `prod` | `workspace` | `prod` | schedule chạy thật hằng ngày, `permissions` gán `CAN_MANAGE` cho `mychivodoi123@gmail.com` |

Cả 3 target hiện dùng **chung 1 workspace** (`dbc-4c2ccca6-b3b8.cloud.databricks.com`),
chỉ khác `catalog`/`schema` — phù hợp cho workspace cá nhân (đặc biệt là
**Databricks Free Edition**, giới hạn 1 workspace/account — xem
[lessons/operations/01-free-edition-limitations.md](lessons/operations/01-free-edition-limitations.md)),
chưa cần tách workspace riêng theo môi trường (xem thêm
[lessons/operations/03-cicd-with-bundles.md](lessons/operations/03-cicd-with-bundles.md)).

## Kiến trúc theo từng phase (xem [roadmap/OVERVIEW.md](roadmap/OVERVIEW.md))

Sơ đồ + bảng environment ở trên là **trạng thái hiện tại** (đã xong setup,
data mẫu `nyctaxi`). Kiến trúc sẽ đổi theo 2 phase:

### Phase 1 · Track 1 (đang làm) — case study CDC/SCD2 (`customers`), chọn dùng 1 catalog

```
fixtures/cdc_demo/customers.csv (bạn tự edit) → snapshot_customers.py
                                                        │
                                                        ▼
                                    UC Volume (snapshots/v1.csv, v2.csv...)
                                                        │
                                                        ▼
                              Bronze — streaming table (Auto Loader, incremental theo file)
                                                        │
                                                        ▼
                      Silver — streaming table (AUTO CDC FROM SNAPSHOT, SCD Type 2, giữ lịch sử)
                                                        │
                                                        ▼
                    Gold — materialized view (filter __END_AT IS NULL, batch, báo cáo)
```
- Vẫn dùng chung catalog `workspace`, tách môi trường bằng schema (không đổi).
- Chạy song song với pipeline `nyctaxi` mẫu có sẵn, không thay thế.
- Vì sao có ACID/time travel/incremental ở đây nhưng không cần khai thác ở
  pipeline `nyctaxi` (data mẫu tĩnh): [lessons/fundamentals/11-acid-timetravel-incremental.md](lessons/fundamentals/11-acid-timetravel-incremental.md).
- Chi tiết đầy đủ: [roadmap/phase-1-track1-cdc-demo.md](roadmap/phase-1-track1-cdc-demo.md).

### Phase 1 · Track 2 — e-commerce project, catalog-per-environment ✅ đã build + deploy thật

⚠️ Đã sửa hiểu nhầm: catalog-per-env **không cần Premium** — verify thật
bằng `CREATE CATALOG` trên chính Free Edition, chạy OK (default managed
storage). Xem [lessons/operations/01-free-edition-limitations.md](lessons/operations/01-free-edition-limitations.md).

```
ecomm_dev / ecomm_staging / ecomm_prod   (3 catalog thật, default storage — không cần Premium)
        │
        ▼
fixtures/ecomm_raw/ (brands, category, date, products, customers, order_items/landing)
        │
        ▼
Bronze — 5 dimension (batch) + order_items (Auto Loader, 92 file/ngày thật, 183K dòng)
        │
        ▼
Silver — join star-schema + fix 7 lỗi data thật (trim, case, đơn vị, dấu phẩy thập phân)
        │
        ▼
Gold — gold_daily_category_revenue (aggregate theo ngày/category/brand)
        │
        ▼
GRANT/REVOKE + Row Filter + Column Mask trên Gold tables (chưa làm — bài tập)
```
- Dùng Pattern A (catalog-per-env) — xem
  [lessons/fundamentals/04-unity-catalog.md](lessons/fundamentals/04-unity-catalog.md).
- Chạy song song với `nyctaxi` demo + case study `customers` CDC (Pattern B, Track 1) — không thay thế, không migrate 2 cái đó.
- Chi tiết đầy đủ (đã deploy + run `TERMINATED SUCCESS`, kể cả 1 gotcha
  thật đã fix): [roadmap/phase-1-track2-ecommerce-project.md](roadmap/phase-1-track2-ecommerce-project.md).

### Phase 2 (chưa làm) — chỉ còn 1 việc: storage thật của bạn

Sau khi sửa hiểu nhầm, Phase 2 thu hẹp lại đúng phần Free Edition **thật
sự** không làm được: tự mang cloud storage của bạn (không phải catalog).

```
Storage Credential (Azure Access Connector / AWS IAM role CỦA BẠN)
        │
        ▼
External Location → ADLS Gen2/S3 container thật (ngoài Databricks)
        │
        ▼
CREATE CATALOG ... MANAGED LOCATION '<external location>'
        (thay vì default managed storage như Phase 1 đang dùng)
```
- Toàn bộ code Bronze/Silver/Gold, GRANT/Row Filter/Column Mask ở Phase 1
  **không đổi gì** — chỉ đổi nơi catalog lưu file vật lý.
- Chi tiết đầy đủ: [roadmap/phase-2-trial-security.md](roadmap/phase-2-trial-security.md).

## Data thật của bạn (khi thay data mẫu ngoài case study CDC)

Muốn thay `samples.nyctaxi.trips` bằng nguồn khác, chỉ cần đổi nguồn đọc
trong `src/my_project_etl/transformations/*.py`, ví dụ:

```python
spark.read.table(f"{catalog}.{schema}.ten_table_that")
```

Kiến trúc job/pipeline phía trên không đổi — chỉ đổi nguồn data ở tầng
transformation đầu tiên.
