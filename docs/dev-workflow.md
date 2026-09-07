# Dev workflow — vòng lặp phát triển hằng ngày

Đây là **quy trình lặp lại** mỗi khi bạn sửa code và muốn đưa lên workspace
kiểm tra — khác với setup ban đầu ([setup.md](setup.md), chỉ chạy 1 lần) và
[roadmap/OVERVIEW.md](roadmap/OVERVIEW.md) (planning cấp cao, không có lệnh).

## 1. Cài/đồng bộ dependencies local (khi `pyproject.toml` đổi)

```powershell
uv sync --dev
```
Tạo/cập nhật `.venv` local (pytest, ruff, databricks-connect...). Không đụng workspace.

## 2. Test local trước (fail sớm, đỡ tốn công deploy sai)

```powershell
uv run pytest
```
Query data thật qua `databricks-connect` — cần đã `databricks auth login`.
Fail ở đây thì sửa trước, không cần lên workspace mới biết sai.

## 3. Validate bundle (nhanh, không tốn gì, không deploy)

```powershell
databricks bundle validate --target dev
```
Chỉ check cú pháp YAML + biến.

## 4. Deploy lên workspace

```powershell
databricks bundle deploy --target dev
```
- Build wheel từ `src/my_project`, upload code, tạo/update job + pipeline.
- **Không tự chạy gì** — chỉ "cài đặt" định nghĩa. Schedule bị pause ở dev
  (`mode: development`).
- Đổi `dev` → `staging`/`prod` để deploy môi trường khác.

## 5. Chạy thử để tạo/cập nhật data

```powershell
databricks bundle run --target dev
```
CLI hỏi chọn resource nếu có nhiều. Thứ tự task chạy theo `depends_on`
khai báo trong [resources/sample_job.job.yml](../resources/sample_job.job.yml).

## 6. Xem kết quả

- **Qua code**: mở [src/my_project_etl/explorations/sample_exploration.ipynb](../src/my_project_etl/explorations/sample_exploration.ipynb), chạy `display(spark.sql(...))`.
- **Qua UI**: Jobs & Pipelines (xem log run) hoặc Catalog Explorer (xem bảng data).

## Gotcha hay gặp khi deploy target mới lần đầu

Job/pipeline có thể fail `SCHEMA_NOT_FOUND` nếu schema của target đó chưa
tồn tại — xem cách fix + giải thích đầy đủ ở
[lessons/operations/05-gotchas-thuc-chien.md](lessons/operations/05-gotchas-thuc-chien.md).

## CI/CD (chưa làm, để sau)

Khi thao tác tay bước 3–5 lặp lại nhiều, xem
[lessons/operations/03-cicd-with-bundles.md](lessons/operations/03-cicd-with-bundles.md)
để tự động hóa qua GitHub Actions.
