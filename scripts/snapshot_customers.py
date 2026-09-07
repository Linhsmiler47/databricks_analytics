"""Chốt 1 snapshot mới từ fixtures/cdc_demo/customers.csv.

Chạy: uv run python scripts/snapshot_customers.py

Chạy sau khi bạn tự tay sửa fixtures/cdc_demo/customers.csv (đổi email,
xóa dòng, thêm dòng...). Copy nguyên trạng thái hiện tại của file đó thành
1 snapshot mới, đánh số tăng dần (v2.csv, v3.csv, ...) trong
fixtures/cdc_demo/snapshots/ — mỗi lần chạy script này = 1 "lần export"
mô phỏng CDC thật.

Xem docs/roadmap/phase-1-free-edition.md mục 1.3-1.5.
"""
import re
import shutil
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "cdc_demo"
CUSTOMERS_CSV = BASE_DIR / "customers.csv"
SNAPSHOTS_DIR = BASE_DIR / "snapshots"


def next_version() -> int:
    versions = []
    for f in SNAPSHOTS_DIR.glob("v*.csv"):
        m = re.match(r"v(\d+)\.csv$", f.name)
        if m:
            versions.append(int(m.group(1)))
    return max(versions, default=0) + 1


def main():
    if not CUSTOMERS_CSV.exists():
        print(f"Không thấy {CUSTOMERS_CSV}.")
        print("Chạy `uv run python scripts/seed_cdc_sample_data.py` trước.")
        return

    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    version = next_version()
    dest = SNAPSHOTS_DIR / f"v{version}.csv"
    shutil.copy(CUSTOMERS_CSV, dest)

    print(f"wrote {dest}")
    print()
    print("Upload lên Volume:")
    print(f"  databricks fs cp {dest} dbfs:/Volumes/workspace/<dev_schema>/raw_customers/snapshots/")


if __name__ == "__main__":
    main()
