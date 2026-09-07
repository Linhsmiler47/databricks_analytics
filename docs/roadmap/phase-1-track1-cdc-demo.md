# Phase 1 · Track 1 — CDC/SCD2 demo (`customers`, data nhỏ tự edit tay)

File này **tự chứa từ A-Z** — chạy từ 1.1 trở xuống là đủ để đưa 1 máy
trắng (của bạn hoặc người khác) tới đúng trạng thái hiện tại của project,
không cần đọc file nào khác trước. Sau khi xong setup (1.1–1.2), việc sửa
code lặp lại hằng ngày thì dùng [dev-workflow.md](../dev-workflow.md).

Workspace: `dbc-4c2ccca6-b3b8.cloud.databricks.com` (Free Edition). Mọi bài
tập dưới đây chạy được đầy đủ trên Free Edition — kể cả Auto Loader và AUTO
CDC/SCD Type 2 (chỉ giới hạn "1 pipeline active/loại", không bị chặn tính
năng, xem [Bài 1 — Free Edition limits](../lessons/operations/01-free-edition-limitations.md)).

Từ mục 1.3 trở đi là 1 case study xuyên suốt: build lại đúng vòng đời 1
bảng "khách hàng" thay đổi theo thời gian — sát với việc thật ở công ty
hơn nhiều so với data mẫu `nyctaxi` tĩnh có sẵn từ template.

## Tickbox tiến độ

- [x] 1.1 — Setup môi trường (tools, auth, deps)
- [x] 1.2 — Environments: schema dev/staging/prod + deploy/run xác nhận
- [ ] 1.3 — Sinh data mẫu CDC
- [ ] 1.4 — Bronze: Auto Loader ingest CSV qua UC Volume
- [ ] 1.5 — Silver: CDC + SCD Type 2 (AUTO CDC API)
- [ ] 1.6 — Gold: tổng hợp phục vụ báo cáo
- [ ] 1.7 — Data quality expectations
- [ ] 1.8 — Parameterization nâng cao
- [ ] 1.9 — Orchestration: nối task Bronze→Silver→Gold
- [ ] 1.10 — Unit test cho từng layer

---

## 1.1 — Setup môi trường

Chạy từ máy trắng + đã `git clone` repo này:

```powershell
# 1. Cài công cụ
winget install -e --id Databricks.DatabricksCLI --accept-source-agreements --accept-package-agreements
python -m pip install uv
```
⚠️ Nếu `databricks`/`uv` không nhận sau khi cài: khởi động lại **toàn bộ**
VS Code (không chỉ tab terminal) — PATH mới chỉ nạp khi VS Code khởi động
lại. Chi tiết: [lessons/operations/05-gotchas-thuc-chien.md](../lessons/operations/05-gotchas-thuc-chien.md).

```powershell
# 2. Xác thực
databricks auth login --host https://dbc-4c2ccca6-b3b8.cloud.databricks.com --profile DEFAULT
databricks current-user me --profile DEFAULT

# 3. Cài dependencies + validate
uv sync --dev
databricks bundle validate --target dev
```

**Tiêu chí xong:** `current-user me` trả về đúng user, `validate` không lỗi.

## 1.2 — Environments: 3 schema + deploy/run xác nhận

3 target `dev`/`staging`/`prod` đã có sẵn trong
[databricks.yml](../../databricks.yml) — cùng catalog `workspace`, khác
schema.

```powershell
# Tạo schema trước khi deploy lần đầu (bắt buộc, xem gotcha bên dưới)
uv run python -c "
from databricks.connect import DatabricksSession
spark = DatabricksSession.builder.serverless(True).getOrCreate()
spark.sql('CREATE SCHEMA IF NOT EXISTS workspace.<your-username>')
spark.sql('CREATE SCHEMA IF NOT EXISTS workspace.staging')
"

# Deploy + chạy thử dev
databricks bundle deploy --target dev
databricks bundle run sample_job --target dev

# Deploy staging
databricks bundle validate --target staging
databricks bundle deploy --target staging
```
(`<your-username>` = phần trước `@` trong email Databricks của bạn, vd
`mychivodoi123`. Schema `prod` tạo tương tự khi thật sự deploy `--target prod`.)

⚠️ **Gotcha thường gặp:** job fail `SCHEMA_NOT_FOUND` nếu quên tạo schema
trước — giải thích đầy đủ ở
[lessons/operations/05-gotchas-thuc-chien.md](../lessons/operations/05-gotchas-thuc-chien.md).

**Tiêu chí xong:** `bundle run sample_job --target dev` trả về
`TERMINATED SUCCESS`.

---

## 1.3 — Data mẫu thay đổi theo thời gian: bạn tự tay edit, không cần kịch bản dựng sẵn

Data thật không tĩnh — nó có insert/update/delete liên tục. Thay vì viết
sẵn kịch bản "ngày 1 thế này, ngày 2 thế kia", cách sát thực tế hơn (và
đúng cách repo tham khảo
[databricks-masterclass](https://github.com/afaqueahmad7117/databricks-masterclass)
làm) là: giữ **1 file CSV sống**, bạn tự tay sửa nó, rồi "chốt" thành
snapshot mới. Pipeline tự so sánh 2 snapshot liền nhau để suy ra
INSERT/UPDATE/DELETE — **không cần cột `operation` nào cả** (khác cách
CDC theo operation-log kiểu Debezium).

```powershell
uv run python scripts/seed_cdc_sample_data.py
```
Chạy 1 lần duy nhất — tạo `fixtures/cdc_demo/customers.csv` (3 khách hàng
khởi điểm) + snapshot đầu `fixtures/cdc_demo/snapshots/v1.csv`.

**Từ giờ, mỗi khi muốn mô phỏng 1 đợt thay đổi:**
1. Tự tay mở `fixtures/cdc_demo/customers.csv`, sửa gì tùy ý — đổi email,
   xóa 1 dòng, thêm 1 dòng mới.
2. Chạy `uv run python scripts/snapshot_customers.py` → sinh
   `snapshots/v2.csv` (rồi `v3.csv`, `v4.csv`... tăng dần mỗi lần chạy).

**Tiêu chí xong:** có ít nhất `v1.csv` + `v2.csv` trong
`fixtures/cdc_demo/snapshots/`, nội dung `v2` khác `v1` theo đúng gì bạn
vừa sửa tay.

## 1.4 — Bronze layer: Auto Loader ingest raw CSV qua UC Volume

> **Vì sao CSV → Volume → table, không đọc thẳng CSV?** Volume = nơi
> Unity Catalog quản lý quyền/audit cho file thô (như 1 "ngăn kéo có
> khóa"); Bronze table (qua Auto Loader) = có ACID + tự nhớ file nào đã
> xử lý rồi (không đọc lại từ đầu mỗi lần). Giải thích đầy đủ + sơ đồ 3
> chặng: [lessons/fundamentals/10-volumes-and-autoloader.md](../lessons/fundamentals/10-volumes-and-autoloader.md).

```sql
-- 1. Tạo volume
CREATE VOLUME IF NOT EXISTS workspace.<dev_schema>.raw_customers;
```
```powershell
# 2. Upload từng snapshot một (mô phỏng "mỗi lần export 1 bản chụp mới")
databricks fs cp fixtures/cdc_demo/snapshots/v1.csv dbfs:/Volumes/workspace/<dev_schema>/raw_customers/snapshots/
```
```python
# 3. src/my_project_etl/transformations/bronze_customers.py
from pyspark import pipelines as dp

@dp.table
def bronze_customers():
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "csv")
        .option("cloudFiles.inferColumnTypes", "true")
        .load("/Volumes/workspace/<dev_schema>/raw_customers/snapshots/")
        .selectExpr("*", "_metadata.file_path as source_file", "current_timestamp() as ingested_at")
    )
```
```powershell
# 4. Deploy + run
databricks bundle deploy --target dev
databricks bundle run --target dev
```

Xác nhận Bronze có 3 dòng (từ `v1.csv`). Upload tiếp `v2.csv`, chạy lại →
Bronze phải có **thêm dòng của `v2`** (union cả 2 file), không đọc lại
`v1.csv` — đây chính là Auto Loader tự detect file mới. Bronze ở đây chỉ
là **bản sao thô của mọi snapshot** (để audit/debug), chưa phải là bảng
"trạng thái hiện tại" — việc đó để Silver (mục 1.5) lo.

**Tiêu chí xong:** Bronze table có thêm dòng đúng theo mỗi snapshot mới upload.

## 1.5 — Silver layer: CDC + SCD Type 2 (AUTO CDC API)

Đây là phần lõi của case study. Lakeflow có API riêng cho đúng kịch bản
"so sánh 2 bản chụp (snapshot) để tự suy ra thay đổi" —
`create_auto_cdc_from_snapshot_flow` — khác với `create_auto_cdc_flow`
(dùng khi nguồn đã có sẵn cột operation kiểu Debezium). Không cần tự viết
`MERGE INTO` tay (khái niệm nền:
[lessons/fundamentals/03-delta-lake.md](../lessons/fundamentals/03-delta-lake.md)).

**Khái niệm nhanh:** SCD Type 1 ghi đè, mất lịch sử. SCD Type 2 **không
ghi đè** — mỗi thay đổi tạo 1 dòng mới, dòng cũ đóng lại bằng `__END_AT`,
nên truy vấn lại được "tại lần snapshot thứ mấy, dữ liệu trông thế nào".

```python
from pyspark import pipelines as dp

# 1. Streaming table đích — PHẢI có __START_AT/__END_AT
dp.create_streaming_table(
    name="silver_customers",
    schema="""
        id INT, name STRING, email STRING,
        __START_AT LONG, __END_AT LONG
    """,
)

# 2. Hàm trả về snapshot "tiếp theo" — đọc lần lượt v1.csv, v2.csv, v3.csv...
#    theo đúng thứ tự đánh số, dừng khi hết file.
def next_customer_snapshot(latest_version):
    next_version = 1 if latest_version is None else latest_version + 1
    path = f"/Volumes/workspace/<dev_schema>/raw_customers/snapshots/v{next_version}.csv"
    try:
        df = spark.read.option("header", True).csv(path)
    except Exception:
        return None  # hết snapshot để xử lý
    return (df, next_version)

# 3. AUTO CDC FROM SNAPSHOT — Lakeflow tự diff 2 snapshot liền nhau,
#    tự suy ra INSERT/UPDATE/DELETE dựa trên "keys", KHÔNG cần cột operation
dp.create_auto_cdc_from_snapshot_flow(
    target="silver_customers",
    source=next_customer_snapshot,
    keys=["id"],
    stored_as_scd_type=2,
)
```
```powershell
databricks bundle deploy --target dev
databricks bundle run --target dev
```

Query `silver_customers` sau khi có `v1.csv` + `v2.csv`. Với ví dụ sửa tay
"đổi email An, xóa Binh, thêm Duy": `id=2` (Binh) → dòng cũ có `__END_AT`
được set (bị coi là xóa vì không còn xuất hiện trong `v2`, dù không có cột
operation nào khai báo điều đó). `id=1` (An) → 2 dòng, dòng email mới có
`__END_AT IS NULL`. `id=4` (Duy) → dòng mới xuất hiện. Tự tay sửa tiếp
`customers.csv`, chạy `snapshot_customers.py` để ra `v3.csv`, upload, chạy
lại pipeline → lịch sử tiếp tục nối dài.

**Tiêu chí xong:** giải thích được vì sao `silver_customers` có nhiều dòng
hơn số khách hàng thật, và tự thêm/sửa/xóa 1 dòng trong `customers.csv` rồi
thấy đúng thay đổi đó phản ánh vào Silver sau khi chạy pipeline.

💡 **Thử thêm (bonus, không bắt buộc):** chạy
`DESCRIBE HISTORY workspace.<schema>.silver_customers` rồi
`SELECT * FROM ... VERSION AS OF 1` — so sánh cảm giác "xem lại quá khứ"
kiểu **time travel** (kỹ thuật, có hạn) với việc query
`WHERE __END_AT IS NULL` kiểu **SCD Type 2** (nghiệp vụ, vĩnh viễn). 2 thứ
dễ nhầm là một — phân biệt kỹ ở
[lessons/fundamentals/11-acid-timetravel-incremental.md](../lessons/fundamentals/11-acid-timetravel-incremental.md).

## 1.6 — Gold layer: tổng hợp phục vụ báo cáo

```python
@dp.table
def gold_customers_current():
    return spark.read.table("silver_customers").filter("__END_AT IS NULL")
```
Pattern chuẩn: Silver giữ toàn bộ lịch sử, Gold chỉ expose trạng thái
hiện tại. Về mặt kỹ thuật, bảng này là 1 **materialized view** (batch,
không streaming) — khác cơ chế incremental với Bronze/Silver ở trên, xem
[lessons/fundamentals/11-acid-timetravel-incremental.md](../lessons/fundamentals/11-acid-timetravel-incremental.md).

## 1.7 — Data quality expectations

```python
@dp.table
@dp.expect_or_drop("valid_id", "id IS NOT NULL")
@dp.expect("valid_email", "email LIKE '%@%'")
def bronze_customers():
    ...
```
`expect` = log cảnh báo; `expect_or_drop` = tự loại dòng vi phạm;
`expect_or_fail` = dừng pipeline. Cố tình sửa 1 email sai định dạng trong
`customers.csv` trước khi chốt snapshot mới (`snapshot_customers.py`), xem
expectation bắt được trong tab Data Quality.

## 1.8 — Parameterization nâng cao

Đã có sẵn cơ chế qua biến `catalog`/`schema`. Bài tập: thêm biến mới
`is_production` (boolean) trong `databricks.yml`, dùng để bật/tắt hành vi
khác nhau giữa môi trường.

## 1.9 — Orchestration: nối nhiều task thành chuỗi

Sửa `resources/sample_job.job.yml` thành chuỗi đúng nghĩa Medallion:
`refresh_pipeline` (Bronze→Silver CDC→Gold) → `notebook_task`, dùng
`depends_on` để ép thứ tự. Thử thêm `run_if`, `max_retries`, 1
`condition_task`.

## 1.10 — Unit test cho từng layer

```python
def test_scd2_close_old_row_on_update(spark):
    # tạo DataFrame giả lập input CDC, assert __END_AT được set đúng
    ...
```
Chạy: `uv run pytest`.

---

**Tiêu chí xong toàn Phase 1:** `uv run pytest` pass hết, `bundle deploy`
sạch cho cả 3 target, và bạn tự tin giải thích Bronze/Silver/Gold + CDC +
SCD Type 2 cho người khác mà không cần nhìn tài liệu — sẵn sàng sang
[Phase 2](phase-2-trial-security.md).
