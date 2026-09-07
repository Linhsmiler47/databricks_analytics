# Setup — chạy 1 lần từ máy trắng

Không phải kế hoạch học, không phải vòng lặp hằng ngày — đây là **bootstrap
toàn bộ repo**, chạy 1 lần (máy mới, hoặc người khác clone repo này). Sau
bước này, việc sửa code lặp lại hằng ngày dùng
[dev-workflow.md](dev-workflow.md); muốn học tiếp thì xem
[roadmap/OVERVIEW.md](roadmap/OVERVIEW.md).

Workspace: `dbc-4c2ccca6-b3b8.cloud.databricks.com` (Free Edition).

## 1. Cài công cụ

```powershell
winget install -e --id Databricks.DatabricksCLI --accept-source-agreements --accept-package-agreements
python -m pip install uv
```
⚠️ Nếu `databricks`/`uv` không nhận sau khi cài: khởi động lại **toàn bộ**
VS Code (không chỉ tab terminal) — PATH mới chỉ nạp khi VS Code khởi động
lại. Chi tiết: [lessons/operations/05-gotchas-thuc-chien.md](lessons/operations/05-gotchas-thuc-chien.md).

## 2. Xác thực + cài dependencies

```powershell
databricks auth login --host https://dbc-4c2ccca6-b3b8.cloud.databricks.com --profile DEFAULT
databricks current-user me --profile DEFAULT

uv sync --dev
databricks bundle validate --target dev --profile DEFAULT
```
**Tiêu chí xong:** `current-user me` trả về đúng user, `validate` không lỗi.

## 3. Tạo schema + deploy + chạy thử (demo `nyctaxi` có sẵn)

```powershell
uv run python -c "
from databricks.connect import DatabricksSession
spark = DatabricksSession.builder.serverless(True).getOrCreate()
spark.sql('CREATE SCHEMA IF NOT EXISTS workspace.<your-username>')
spark.sql('CREATE SCHEMA IF NOT EXISTS workspace.staging')
"

databricks bundle deploy --target dev --profile DEFAULT
databricks bundle run sample_job --target dev --profile DEFAULT
```
(`<your-username>` = phần trước `@` trong email Databricks của bạn, vd
`mychivodoi123`. Schema `prod` tạo tương tự khi thật sự deploy `--target prod`.)

⚠️ **Gotcha thường gặp:** job fail `SCHEMA_NOT_FOUND` nếu quên tạo schema
trước — giải thích đầy đủ ở
[lessons/operations/05-gotchas-thuc-chien.md](lessons/operations/05-gotchas-thuc-chien.md).

**Tiêu chí xong:** `bundle run sample_job --target dev` trả về
`TERMINATED SUCCESS` — pipeline `nyctaxi` (`sample_trips_my_project` →
`sample_zones_my_project`) chạy được, xác nhận toàn bộ hạ tầng cơ bản OK.

## 4. (Tùy chọn) Deploy staging

```powershell
databricks bundle validate --target staging --profile DEFAULT
databricks bundle deploy --target staging --profile DEFAULT
```

## Bước tiếp theo

Setup xong = sẵn sàng cho [roadmap/phase-1-ecommerce.md](roadmap/phase-1-ecommerce.md) —
project e-commerce đầy đủ (catalog riêng, data thật, GRANT/Row Filter/
Column Mask) — xem [roadmap/OVERVIEW.md](roadmap/OVERVIEW.md) để biết
trạng thái hiện tại.
