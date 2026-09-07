"""Seed script — tạo file CSV "sống" đầu tiên để luyện CDC kiểu snapshot-diff.

Chạy: uv run python scripts/seed_cdc_sample_data.py

Tạo fixtures/cdc_demo/customers.csv (3 khách hàng khởi điểm, bạn sẽ tự tay
sửa file này sau) và lưu bản chụp đầu tiên vào fixtures/cdc_demo/snapshots/v1.csv.

Workflow sau khi chạy script này 1 lần (không cần chạy lại):
  1. Tự tay sửa fixtures/cdc_demo/customers.csv — đổi 1 email, xóa 1 dòng,
     thêm 1 dòng mới... (mô phỏng thay đổi thật theo thời gian).
  2. Chạy `uv run python scripts/snapshot_customers.py` để "chốt" bản chụp
     mới (v2.csv, v3.csv, ...) từ đúng nội dung hiện tại của customers.csv.
  3. Upload snapshot mới lên Volume, chạy lại pipeline.

Lakeflow (`create_auto_cdc_from_snapshot_flow`) tự so sánh 2 snapshot liền
nhau và suy ra INSERT/UPDATE/DELETE — không cần cột "operation" nào cả.
Xem docs/roadmap/phase-1-free-edition.md mục 1.3-1.5.
"""
import csv
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "cdc_demo"
CUSTOMERS_CSV = BASE_DIR / "customers.csv"
SNAPSHOTS_DIR = BASE_DIR / "snapshots"
FIELDNAMES = ["id", "name", "email"]

STARTER_ROWS = [
    {"id": 1, "name": "An", "email": "an@x.com"},
    {"id": 2, "name": "Binh", "email": "binh@x.com"},
    {"id": 3, "name": "Chi", "email": "chi@x.com"},
]


def write_csv(path: Path, rows: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def main():
    if CUSTOMERS_CSV.exists():
        print(f"{CUSTOMERS_CSV} đã tồn tại — không ghi đè.")
        print("Xóa file này (và fixtures/cdc_demo/snapshots/) nếu muốn seed lại từ đầu.")
        return

    write_csv(CUSTOMERS_CSV, STARTER_ROWS)
    write_csv(SNAPSHOTS_DIR / "v1.csv", STARTER_ROWS)
    print(f"wrote {CUSTOMERS_CSV}")
    print(f"wrote {SNAPSHOTS_DIR / 'v1.csv'}")
    print()
    print("Tiếp theo: tự sửa tay fixtures/cdc_demo/customers.csv, rồi chạy:")
    print("  uv run python scripts/snapshot_customers.py")


if __name__ == "__main__":
    main()
