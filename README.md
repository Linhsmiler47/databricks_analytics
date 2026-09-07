# databricks_analytics

This is a place to learn Databricks.

## About

This repository is used to learn Databricks.

## Topics

- Databricks notebooks
- SQL
- PySpark
- Data Engineering
- Databricks Asset Bundles (Declarative Automation Bundles / IaC)

## Project layout

This repo is a Databricks Asset Bundle (generated via `databricks bundle init default-python`, package name `my_project`):

- `src/`: Python source code for this project.
  - `src/my_project/`: Shared Python code used by jobs and pipelines.
  - `src/my_project_etl/`: Lakeflow pipeline transformations — `nyctaxi` demo (catalog `workspace`, verify setup cơ bản).
  - `src/ecomm_etl/`: Project chính — e-commerce (catalog-per-env `ecomm_dev`/`ecomm_staging`/`ecomm_prod`) — `transformations/bronze|gold/` (Lakeflow) + `scripts/` (plain Delta Table + Job, xem [docs/lessons/fundamentals/13-delta-table-job-vs-lakeflow.md](docs/lessons/fundamentals/13-delta-table-job-vs-lakeflow.md)).
- `resources/`: Resource configurations (jobs, pipelines, etc.) — `sample_job`/`my_project_etl` (demo `nyctaxi`) và `ecomm_job`/`ecomm_bronze|gold_pipeline` (project chính).
- `tests/`: Unit tests for the shared Python code.
- `fixtures/`: Sample/test data sets.
  - `fixtures/ecomm_raw/` — dataset e-commerce thật (star schema: brands/category/date/products/customers + order_items dạng landing 92 file/ngày, ~26MB, `customers.csv` đã lọc chỉ giữ ID có trong order_items).
- `scripts/`: Script tiện ích chạy local (không deploy lên Databricks) — `import_ecomm_raw_data.py` (copy + lọc dataset e-commerce từ nguồn ngoài repo).
- `databricks.yml`: Bundle definition (targets: `dev`, `staging`, `prod`; biến `catalog`/`schema` cho demo `nyctaxi`, `ecomm_catalog` cho e-commerce).
- `docs/`: xem [docs/INDEX.md](docs/INDEX.md) — setup, kiến trúc, lessons, roadmap học.

## Getting started

Choose how you want to work on this project:

(a) Directly in your Databricks workspace, see
    https://docs.databricks.com/dev-tools/bundles/workspace.

(b) Locally with an IDE like Cursor or VS Code, see
    https://docs.databricks.com/dev-tools/vscode-ext.html.

(c) With command line tools, see https://docs.databricks.com/dev-tools/cli/databricks-cli.html

If you're developing with an IDE, dependencies for this project should be installed using uv:

- Make sure you have the UV package manager installed: https://docs.astral.sh/uv/getting-started/installation/.
- Run `uv sync --dev` to install the project's dependencies.

### Using this project with the CLI

1. Authenticate to your Databricks workspace, if you have not done so already:
   ```
   databricks auth login --host https://dbc-4c2ccca6-b3b8.cloud.databricks.com --profile DEFAULT
   ```

2. To deploy a development copy of this project, type:
   ```
   databricks bundle deploy --target dev
   ```
   ("dev" is the default target, so `--target` is optional.)

   This deploys everything defined for this project. For example, the default
   template deploys a pipeline called `[dev yourname] my_project_etl` to your
   workspace. Find it under **Jobs & Pipelines** in the workspace UI.

3. Similarly, to deploy a production copy:
   ```
   databricks bundle deploy --target prod
   ```
   The default template includes a job that runs the pipeline every day
   (`resources/sample_job.job.yml`). The schedule is paused when deploying
   in development mode.

4. To run a job or pipeline:
   ```
   databricks bundle run
   ```

5. To run tests locally:
   ```
   uv run pytest
   ```
