# Phase 1 · Track 2 — E-commerce project (data thật, catalog-per-environment)

File này tự chứa — đã **build và deploy thật**, không phải chỉ là kế
hoạch. Dùng data thật (`fixtures/ecomm_raw/`, xem
[README.md](../../README.md)) thay vì data đồ chơi 3 dòng của Track 1
(`fixtures/cdc_demo/`) — 2 track chạy song song, không cái nào thay cái nào.

Khác biệt lớn nhất so với Track 1: dùng **Pattern A — catalog-per-
environment** (`ecomm_dev`/`ecomm_staging`/`ecomm_prod`), không dùng
schema-per-environment nữa. Lý do đổi được: đã verify **catalog-per-env
không cần Premium** — xem
[lessons/operations/01-free-edition-limitations.md](../lessons/operations/01-free-edition-limitations.md).

## ⚠️ Đã restructure lại 2.3-2.5 theo khung quyết định "công nghệ nào hợp layer nào"

Áp đúng 3 case bạn đưa ra (SAP nightly MERGE / Kafka continuous / dashboard
aggregate nặng) vào từng bảng thật — không ép 1 công nghệ cho mọi layer:
- `bronze_order_items` (92 file/ngày) — **giữ** Streaming Table (giống case Kafka).
- 5 dimension Bronze + toàn bộ Silver — **đổi** sang Delta Table + Job/Notebook
  (script thường, `MERGE INTO` cho `silver_order_items`) — giống case SAP.
- `gold_daily_category_revenue` — **giữ** Materialized View (giống case dashboard aggregate nặng).

Chi tiết + code: [lessons/fundamentals/13-delta-table-job-vs-lakeflow.md](../lessons/fundamentals/13-delta-table-job-vs-lakeflow.md).

**Trạng thái thật (không phóng đại)**: code đã viết xong, `bundle deploy`
đã thành công (xóa `ecomm_silver_pipeline` cũ). Chạy job để verify thì gặp
2 vấn đề — 1 bug thật (5 bảng dimension cũ còn sót dạng `MATERIALIZED_VIEW`
trong `bronze`, xung đột với `saveAsTable` mới, cần `DROP TABLE` trước) và
1 giới hạn thật (`RESOURCE_EXHAUSTED` — **hết quota serverless compute
Free Edition** do dùng quá nhiều trong ngày, đúng "fair usage policy" đã
ghi ở [Bài 2](../lessons/operations/01-free-edition-limitations.md), lần
đầu gặp thật). **Chưa verify chạy end-to-end thành công** — xem mục 2.3
bên dưới để biết chính xác cần làm gì khi quota hồi lại.

## Tickbox tiến độ

- [x] 2.1 — Tạo 3 catalog thật (`ecomm_dev`/`ecomm_staging`/`ecomm_prod`) + biến `ecomm_catalog` trong `databricks.yml`
- [x] 2.2 — Tạo schema `bronze`/`silver`/`gold` + Volume, upload data lên `ecomm_dev`
- [x] 2.3 — Code Bronze (script + pipeline) đã viết + deploy — ⏸️ **chưa verify chạy được** (chờ quota + dọn bảng cũ, xem chi tiết bên dưới)
- [x] 2.4 — Code Silver (`MERGE INTO`) đã viết + deploy — ⏸️ **chưa verify** (phụ thuộc 2.3 chạy xong trước)
- [x] 2.5 — Gold `gold_daily_category_revenue` (Materialized View, không đổi) — ⏸️ **chưa verify lại sau restructure**
- [ ] 2.6 — ⏸️ Chưa urgent: lặp lại 2.1–2.5 cho `staging`/`prod` (không sát công việc thật nếu bạn chỉ maintain 1 catalog prod — để sau)
- [x] 2.7 — GRANT / REVOKE phân quyền — **đã chạy thật, có 1 gotcha quan trọng (owner bypass)**
- [x] 2.8 — Row Filter — **đã chạy thật, tự thấy đúng góc nhìn non-admin**
- [x] 2.9 — Column Mask — **đã chạy thật, tự thấy đúng góc nhìn non-admin**
- [x] 2.10 — Audit log — **đã kiểm tra, có ghi nhận (delay vài phút)**
- [x] 2.11 — ABAC (tag+policy) trên materialized view + verify bằng Service Principal độc lập — **đã chạy thật**

## 🔧 Cheat sheet lệnh

| Bước | Lệnh chính |
|---|---|
| 2.1–2.2 (đã làm, để tham khảo) | `CREATE CATALOG`/`CREATE SCHEMA`/`CREATE VOLUME` qua databricks-connect, `databricks fs cp -r fixtures/ecomm_raw/ dbfs:/Volumes/ecomm_dev/bronze/raw_files/` |
| 2.3–2.5 (code xong, ⏸️ chưa verify chạy) | `databricks bundle deploy --target dev --profile DEFAULT` → (nếu lỗi `MATERIALIZED_VIEW` conflict: `DROP SCHEMA ecomm_dev.bronze CASCADE` trước) → `databricks bundle run ecomm_job --target dev --profile DEFAULT` |
| 2.6 (chưa urgent) | Lặp lại với `--target staging` / `--target prod` (nhớ tạo schema/volume/upload data cho catalog đó trước) |
| 2.7 (đã làm) | `GRANT USE CATALOG ON CATALOG ecomm_dev TO ...` (tách riêng khỏi GRANT cấp schema) |
| 2.8 (đã làm) | `CREATE FUNCTION ... RETURN ...` → `ALTER TABLE bronze_order_items SET ROW FILTER ...` (chỉ áp được lên table thật, không áp lên materialized view) |
| 2.9 (đã làm) | `CREATE FUNCTION ... RETURN CASE WHEN ...` → `ALTER TABLE bronze_order_items ALTER COLUMN ... SET MASK ...` |
| 2.10 (đã làm, có delay) | `SELECT * FROM system.access.audit` (có ghi nhận, delay vài phút) + tab Lineage trong Catalog Explorer (chưa xem, cần UI) |
| 2.11 (đã làm) | `CREATE GOVERNED TAG` → `ALTER TABLE ... SET TAGS` → `CREATE POLICY ... MATCH COLUMNS has_tag(...)` — áp được lên materialized view; verify bằng `databricks service-principals create` + `service-principal-secrets-proxy create` |

## 2.1 — 3 catalog thật + biến bundle

```sql
CREATE CATALOG IF NOT EXISTS ecomm_dev;
CREATE CATALOG IF NOT EXISTS ecomm_staging;
CREATE CATALOG IF NOT EXISTS ecomm_prod;
```
Dùng **default managed storage** — không cần Storage Credential/External
Location (đó là việc của [Phase 2](phase-2-trial-security.md)).

[databricks.yml](../../databricks.yml) có thêm biến `ecomm_catalog`, set
theo từng target (`ecomm_dev` cho `dev`, v.v.) — tách biệt hoàn toàn với
biến `catalog`/`schema` cũ (vẫn phục vụ Track 1 + `nyctaxi` demo).

## 2.2 — Schema, Volume, upload data

```sql
CREATE SCHEMA IF NOT EXISTS ecomm_dev.bronze;
CREATE SCHEMA IF NOT EXISTS ecomm_dev.silver;
CREATE SCHEMA IF NOT EXISTS ecomm_dev.gold;
CREATE VOLUME IF NOT EXISTS ecomm_dev.bronze.raw_files;
```
```powershell
databricks fs cp -r fixtures/ecomm_raw/ dbfs:/Volumes/ecomm_dev/bronze/raw_files/ --overwrite
```
3 schema tương ứng 3 layer Medallion (khác Track 1 — Track 1 gộp chung 1
schema, prefix `bronze_`/`silver_`/`gold_`; ở đây tách hẳn schema vì có
nhiều bảng hơn, tách schema dễ quản lý permission theo layer hơn — xem
GRANT ở mục 2.7 bên dưới).

## 2.3 — Bronze: 1 pipeline (order_items) + 1 script (5 dimension)

**Kiến trúc hiện tại** (sau khi áp khung quyết định, xem banner đầu file):
- `ecomm_bronze_pipeline` (Lakeflow, `resources/ecomm_bronze.pipeline.yml`) —
  **chỉ còn** `order_items`, qua Auto Loader thật với 92 file. Ra
  `STREAMING_TABLE`.
- `refresh_bronze_dimensions.py` (script thường, KHÔNG qua Lakeflow) — 5
  dimension (brands/category/date/products/customers), mỗi lần chạy
  `CREATE OR REPLACE TABLE` (full refresh, vì data nguồn là export lại
  toàn bộ, không có gì để MERGE). Ra `TABLE` thật.

Catalog/Volume path thay đổi theo môi trường — pipeline đọc qua
`configuration:`, script đọc qua `--catalog` (argparse, giống `main.py` ở
Track 1):
```yaml
# resources/ecomm_bronze.pipeline.yml
configuration:
  ecomm_catalog: ${var.ecomm_catalog}
```
```python
# resources/ecomm_job.job.yml — spark_python_task
parameters: ["--catalog", "${var.ecomm_catalog}"]
```

```powershell
databricks bundle deploy --target dev --profile DEFAULT
databricks bundle run ecomm_job --target dev --profile DEFAULT
```

⚠️ **Chưa verify chạy thành công** — 2 vấn đề gặp khi chạy lần đầu sau
restructure:
1. **Bug thật**: 5 bảng dimension cũ (từ kiến trúc Lakeflow trước đây) còn
   sót dạng `MATERIALIZED_VIEW` trong `ecomm_dev.bronze` — `saveAsTable`
   mới không ghi đè được lên loại khác, báo lỗi
   `UC_REQUEST_URL_REQUIRED_FOR_TABLE_TYPE`. **Cách fix**: `DROP TABLE`
   (hoặc `DROP SCHEMA ... CASCADE`) 5 bảng cũ trước khi chạy lại.
2. **Giới hạn thật, không phải bug**: `RESOURCE_EXHAUSTED` — hết quota
   serverless compute Free Edition do dùng quá nhiều trong ngày (đúng
   "fair usage policy" ở [Bài 2](../lessons/operations/01-free-edition-limitations.md)).
   Không có cách "fix" ngoài chờ quota hồi (có thể vài giờ tới hết ngày).

**Việc cần làm khi quota hồi:**
```sql
DROP SCHEMA IF EXISTS ecomm_dev.bronze CASCADE;  -- xóa sạch bảng cũ lẫn volume config, tạo lại schema/volume theo mục 2.2
```
Rồi chạy lại `databricks bundle run ecomm_job --target dev --profile DEFAULT`.

## 2.4 — Silver: 7 lỗi data thật đã fix + MERGE INTO thật

Khảo sát trực tiếp data gốc phát hiện 7 vấn đề, mỗi cái có rule fix cụ thể
trong [src/ecomm_etl/scripts/refresh_silver.py](../../src/ecomm_etl/scripts/refresh_silver.py)
(script thường, không qua Lakeflow — 5 dimension ghi `CREATE OR REPLACE
TABLE`, riêng `silver_order_items` ghi bằng **`MERGE INTO`** thật theo
khóa `(order_id, item_seq)`, đúng pattern "ETL đêm rồi MERGE" — xem
[Bài 13](../lessons/fundamentals/13-delta-table-job-vs-lakeflow.md)):

| # | Bảng | Lỗi | Cách fix |
|---|---|---|---|
| 1 | `brands` | `brand_name` có khoảng trắng thừa (`"  NovaWave "`) | `trim()` |
| 2 | `brands`/`products` | `brand_code` **khác case** giữa 2 bảng (`ACME` vs `acme`) — join sẽ fail nếu không fix | `lower(trim())` cả 2 bên |
| 3 | `date` | `day_name` không đồng nhất case (`FRIDAY` vs `friday`) | `upper(trim())` |
| 4 | `date` | `week_of_year` **toàn bộ 95 dòng đều âm** (-22 đến -44) | Không filter — chỉ log cảnh báo (xem gotcha bên dưới) |
| 5 | `products` | `weight_grams` là string kèm đơn vị (`"305g"`) | `regexp_replace` bỏ ký tự không phải số, cast double |
| 6 | `products` | `length_cm`/`width_cm`/`height_cm` dùng dấu phẩy thập phân (`"22,2"`) | `regexp_replace(',', '.')`, cast double |
| 7 | `order_items` | `discount_pct` là string kèm `%` (`"10%"`) | `regexp_replace('%','')`, cast double, chia 100 |

### ⚠️ Gotcha thật gặp khi build bằng Lakeflow (bài học vẫn còn giá trị dù code đã đổi)

Lần đầu viết `silver_date` **trong bản Lakeflow cũ**, dùng
`@dp.expect_or_drop("valid_week_of_year", "week_of_year BETWEEN 1 AND 53")`
— deploy chạy `SUCCESS` nhưng `silver_date` **rỗng hoàn toàn** (0 dòng),
kéo theo Gold bị `NULL` hết cột `day_name`/`quarter`. Nguyên nhân:
`expect_or_drop` loại theo **dòng**, mà **100% dòng** đều có `week_of_year`
âm — mất trắng cả bảng, kể cả cột `day_name` vẫn tốt cũng bị cuốn theo.

**Bài học** (vẫn áp dụng dù giờ không còn dùng `@dp.expect*` nữa — script
thường ở mục này chỉ `print()` cảnh báo thay vì filter): quyết định
"loại bỏ hoàn toàn 1 dòng vì 1 cột sai" hay "chỉ cảnh báo, giữ dòng" phải
dựa trên **tỷ lệ vi phạm thật** và **cột đó có thật sự cần dùng ở downstream
không** — không phải chọn theo cảm tính hay theo "mặc định nghiêm ngặt".

## 2.5 — Gold: `gold_daily_category_revenue` (không đổi — vẫn Materialized View)

Join `silver_order_items` với `silver_date`, group by ngày/category/brand,
tính `revenue`, `line_items`, `orders` (distinct). Xem
[gold/daily_revenue.py](../../src/ecomm_etl/transformations/gold/daily_revenue.py) —
đây là bảng **duy nhất không đổi** sau restructure, vì đúng case "join +
aggregate nặng cho dashboard" bạn nêu — Materialized View vẫn là lựa chọn
đúng. Chỉ khác: giờ đọc từ `silver_order_items`/`silver_date` là **plain
Delta Table** (do `refresh_silver.py` tạo) thay vì materialized view như
trước — Lakeflow đọc bình thường, không quan tâm bảng nguồn tạo bằng cách
nào.

⏸️ **Chưa verify lại** sau restructure — phụ thuộc 2.3/2.4 chạy xong trước
(quota compute hiện đang hết, xem mục 2.3).

## 2.6 — ⏸️ Chưa urgent: lặp lại cho staging/prod

`databricks bundle deploy` đã tạo resource cho cả 3 target, nhưng
**schema/volume/data chỉ mới setup ở `ecomm_dev`**. Nếu công việc thật của
bạn là **maintain 1 catalog prod có sẵn** (không tự tay promote code qua
nhiều môi trường), bước này **không sát nhu cầu** — để sau, ưu tiên luyện
2.7-2.10 trước (đúng kỹ năng "maintain trong prod"). Khi cần, lệnh y hệt
2.1-2.5, chỉ đổi `ecomm_dev` → `ecomm_staging`/`ecomm_prod`:
```powershell
databricks fs cp -r fixtures/ecomm_raw/ dbfs:/Volumes/ecomm_staging/bronze/raw_files/
databricks bundle run ecomm_job --target staging
```

## 2.7 — GRANT / REVOKE phân quyền ✅ đã chạy thật

```sql
GRANT USE CATALOG ON CATALOG ecomm_dev TO `account users`;
GRANT USE SCHEMA, SELECT ON SCHEMA ecomm_dev.gold TO `account users`;
REVOKE ALL PRIVILEGES ON SCHEMA ecomm_dev.bronze FROM `account users`;
```

⚠️ **Gotcha thật (khác lý thuyết ở chỗ này)**: cú pháp đầu tiên thử
`GRANT USE CATALOG, USE SCHEMA, SELECT ON SCHEMA ...` bị lỗi
`PRIVILEGE_NOT_APPLICABLE_TO_ENTITY` — vì **`USE CATALOG` chỉ gán được ở
cấp CATALOG**, không gán được ở cấp SCHEMA. Phải tách 2 câu GRANT riêng
(1 câu ở cấp catalog, 1 câu ở cấp schema) như trên.

⚠️ **Gotcha thứ 2, quan trọng hơn**: sau khi `REVOKE` quyền đọc `bronze`
khỏi nhóm `account users`, tôi (chính là người tạo catalog) **vẫn đọc được
`bronze` bình thường** — không bị chặn. Lý do: tôi là **owner** của
catalog/schema (người tạo ra nó) — Unity Catalog cho owner quyền truy cập
mặc định, **REVOKE nhắm vào 1 nhóm khác không lấy mất quyền của owner**.

**Bài học:** muốn tự kiểm chứng REVOKE có tác dụng, phải test bằng 1
identity **không phải owner** — GRANT/REVOKE của bạn chỉ thực sự "cảm nhận
được" khi bạn là người bị áp luật, không phải người ban hành nó. Đã verify
lại đúng bằng service principal độc lập ở mục 2.11 bên dưới
— REVOKE chặn thật (`INSUFFICIENT_PERMISSIONS`), không còn nghi ngờ gì.

## 2.8 — Row Filter ✅ đã chạy thật, tự thấy đúng góc nhìn non-admin

⚠️ **Gotcha thật thứ 3**: định áp Row Filter lên
`gold_daily_category_revenue` trước — bị lỗi
`EXPECT_TABLE_NOT_VIEW`. Lý do: `ALTER TABLE ... SET ROW FILTER` chỉ áp
được lên **TABLE thật**, không áp được lên **VIEW**. Kiểm tra bằng
`DESCRIBE EXTENDED <table>` phát hiện: mọi bảng đọc batch (`spark.read...`,
không phải `spark.readStream...`) đều là `MATERIALIZED_VIEW`, chỉ
`bronze_order_items` (dùng Auto Loader) là `STREAMING_TABLE` — bảng thật
duy nhất trong toàn bộ project này. Đây chính là hệ quả thực tế của khái
niệm ở [Bài 11 — ACID/Time Travel/Incremental](../lessons/fundamentals/11-acid-timetravel-incremental.md)
(Bronze/Silver batch = materialized view, không phải table).

→ Áp Row Filter lên `bronze_order_items` thay vì Gold:

```sql
CREATE OR REPLACE FUNCTION ecomm_dev.bronze.channel_row_filter(channel STRING)
RETURN IS_ACCOUNT_GROUP_MEMBER('admins') OR channel != 'app';

ALTER TABLE ecomm_dev.bronze.bronze_order_items
SET ROW FILTER ecomm_dev.bronze.channel_row_filter ON (channel);
```

**Kết quả thật** (tôi xác nhận **không** thuộc nhóm `admins` — dùng
`SELECT is_account_group_member('admins')`, trả về `false` — nên tự tôi
chính là "non-admin" cần test, không cần giả lập user thứ 2):

| | Trước filter | Sau filter (chính tôi, non-admin) |
|---|---|---|
| Tổng dòng | 183,378 | 82,390 |
| `channel` thấy được | `app` (100,988) + `web` (82,390) | chỉ `web` |

Toàn bộ 100,988 dòng `channel='app'` biến mất khỏi kết quả — đúng như thiết kế.

## 2.9 — Column Mask ✅ đã chạy thật

```sql
CREATE OR REPLACE FUNCTION ecomm_dev.bronze.customer_id_mask(customer_id STRING)
RETURN CASE WHEN IS_ACCOUNT_GROUP_MEMBER('admins') THEN customer_id ELSE '***MASKED***' END;

ALTER TABLE ecomm_dev.bronze.bronze_order_items
ALTER COLUMN customer_id SET MASK ecomm_dev.bronze.customer_id_mask;
```

**Kết quả thật** (query bằng chính identity non-admin của tôi):
```
customer_id    order_id  channel
***MASKED***   650510    web
***MASKED***   650511    web
```

## 2.10 — Audit log ✅ đã kiểm tra

```sql
SELECT event_time, action_name
FROM system.access.audit
WHERE event_time >= current_timestamp() - INTERVAL 15 MINUTES
```
Có ghi nhận `createFunction` (2 function vừa tạo ở 2.8/2.9), nhưng
**GRANT/ALTER TABLE chưa xuất hiện ngay** — audit log trên Databricks có
độ trễ ingest (thường vài phút tới lâu hơn), không phải real-time 100%.
Nếu cần audit ngay lập tức cho việc gì gấp, đừng chỉ dựa vào query
`system.access.audit` — kiểm tra thêm qua UI (Account Console → Audit log)
hoặc chờ vài phút rồi query lại.

**Lineage** (chưa verify): Catalog Explorer → `gold_daily_category_
revenue` → tab Lineage — xem sơ đồ tự động Bronze→Silver→Gold, so với sơ
đồ ở mục 2.3–2.5. Việc này cần mở UI, không làm được qua CLI/SQL nên để
bạn tự xem.

## 2.11 — ABAC (tag + policy): fix đúng chỗ Row Filter/Mask cũ bị fail trên materialized view ✅ đã chạy thật

Mục 2.8 phát hiện Row Filter/Mask kiểu cũ không áp được lên materialized
view (đa số bảng trong project này). Cách giải quyết đúng: **ABAC**
(Attribute-Based Access Control) — gắn tag lên cột rồi viết 1 policy áp
dụng cho mọi bảng có tag đó, kể cả materialized view. Giải thích đầy đủ +
cú pháp: [lessons/fundamentals/12-permissions-hierarchy-and-abac.md](../lessons/fundamentals/12-permissions-hierarchy-and-abac.md).

**Đã áp thật lên `bronze_customers` (materialized view) — trước đây
KHÔNG thể áp Row Filter/Mask kiểu cũ lên bảng này:**
```sql
ALTER TABLE ecomm_dev.bronze.bronze_customers
ALTER COLUMN phone SET TAGS ('class.phone_number' = '');  -- dùng tag PII có sẵn

CREATE POLICY mask_phone_policy
ON CATALOG ecomm_dev
COLUMN MASK ecomm_dev.bronze.mask_phone
TO `account users`
FOR TABLES
MATCH COLUMNS has_tag('class.phone_number') AS col
ON COLUMN col;
```
**Kết quả thật**: `SELECT phone FROM ecomm_dev.bronze.bronze_customers` →
`***` — mask hoạt động trên materialized view, đúng như ABAC hứa hẹn.

📌 **Lưu ý sau restructure ở mục 2.3**: `bronze_customers` giờ chuyển
thành plain `TABLE` (qua `refresh_bronze_dimensions.py`, không còn là
materialized view). ABAC vẫn hoạt động bình thường trên cả 3 loại
(`TABLE`/`STREAMING_TABLE`/`MATERIALIZED_VIEW` — xem [Bài 12](../lessons/fundamentals/12-permissions-hierarchy-and-abac.md)),
policy/tag không cần đổi gì. Bằng chứng "ABAC chạy trên materialized view"
giờ xem tốt nhất ở `gold_daily_category_revenue` (mục dưới), vì đó là
bảng duy nhất còn giữ nguyên là Materialized View.

### Verify lại toàn bộ bằng Service Principal — identity hoàn toàn độc lập

Test bằng chính mình (mục 2.7-2.9) có lỗ hổng: mình là **owner**, không
phải người bị áp luật thật. Tạo 1 service principal thật để test độc lập
100% (không cần mượn email ai):
```powershell
databricks service-principals create --display-name "test-non-admin-sp" --profile DEFAULT
databricks service-principal-secrets-proxy create <id> --profile DEFAULT
# thêm profile [test_sp] vào ~/.databrickscfg với client_id/client_secret vừa sinh
```
```powershell
$env:DATABRICKS_CONFIG_PROFILE = "test_sp"
uv run python -c "..."   # query bằng identity SP, không phải bạn
```

**Kết quả xác nhận bằng SP (không phải owner, không phải mình đoán)**:
- `gold_daily_category_revenue` → đúng 7/8 category (Row Filter ABAC hoạt động thật với identity ngoài)
- `bronze_customers` (schema `bronze`) → `INSUFFICIENT_PERMISSIONS` —
  REVOKE ở mục 2.7 chặn thật với identity không phải owner, khác hẳn lúc
  test bằng chính mình.

Cách này dùng được y hệt cho cả "1 catalog/3 schema" lẫn "3 catalog" —
chỉ đổi `catalog.schema.table` trong lệnh GRANT/CREATE POLICY, cơ chế
không đổi.

---

**Tiêu chí xong toàn Track 2:** giải thích được cho người khác 7 lỗi data
đã fix, vì sao chọn `expect` thay vì `expect_or_drop`, 3 gotcha ở mục
2.7-2.8, và vì sao ABAC (không phải Row Filter/Mask kiểu cũ) mới là cách
đúng để bảo mật hầu hết bảng trong 1 Lakeflow pipeline.
