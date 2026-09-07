"""Import script — copy dataset e-commerce thật từ nguồn ngoài repo.

Chạy: uv run python scripts/import_ecomm_raw_data.py

Copy từ SOURCE_DIR (đường dẫn ngoài repo, sửa hằng số bên dưới nếu data
nằm chỗ khác trên máy bạn) vào fixtures/ecomm_raw/. Dataset: star schema
thật — dimension (brands, category, date, products, customers) + fact
(order_items dạng landing, 1 file/ngày) — dùng cho bài tập Bronze/Silver/
Gold quy mô lớn hơn (Auto Loader thật với nhiều file, star-schema join,
data cleaning trên data thật có lỗi định dạng).

customers.csv được LỌC BỚT: chỉ giữ customer_id có xuất hiện trong
order_items (300K → ~88K dòng) — không mất join nào vì order_items giữ
nguyên 100%. products/brands/category/date giữ nguyên (đã gần như được
order_items tham chiếu hết, lọc không giảm được bao nhiêu).

Xem docs/roadmap/phase-1-free-edition.md.
"""
import csv
import shutil
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SOURCE_DIR = Path(r"D:\databrick-mini-course-end-to-end-project\project_assets\project_assets\0_data\ecomm-raw-data")
DEST_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "ecomm_raw"


def copy_full(name: str) -> None:
    src = SOURCE_DIR / name / f"{name}.csv"
    dest_dir = DEST_DIR / name
    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(src, dest_dir / f"{name}.csv")
    print(f"copied {src} -> {dest_dir / f'{name}.csv'}")


def copy_order_items() -> None:
    src_dir = SOURCE_DIR / "order_items" / "landing"
    dest_dir = DEST_DIR / "order_items" / "landing"
    dest_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(src_dir.glob("*.csv"))
    for f in files:
        shutil.copy(f, dest_dir / f.name)
    print(f"copied {len(files)} order_items files -> {dest_dir}")


def copy_customers_filtered() -> None:
    """Copy customers.csv, chỉ giữ customer_id có xuất hiện trong order_items đã copy."""
    referenced_ids = set()
    order_items_dir = DEST_DIR / "order_items" / "landing"
    for f in order_items_dir.glob("*.csv"):
        with open(f, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                referenced_ids.add(row["customer_id"])

    src = SOURCE_DIR / "customers" / "customers.csv"
    dest_dir = DEST_DIR / "customers"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "customers.csv"

    kept = 0
    total = 0
    with open(src, newline="", encoding="utf-8") as fh_in, open(dest, "w", newline="", encoding="utf-8") as fh_out:
        reader = csv.DictReader(fh_in)
        writer = csv.DictWriter(fh_out, fieldnames=reader.fieldnames)
        writer.writeheader()
        for row in reader:
            total += 1
            if row["customer_id"] in referenced_ids:
                writer.writerow(row)
                kept += 1

    print(f"customers.csv: giữ {kept}/{total} dòng (chỉ customer_id xuất hiện trong order_items)")


def main():
    if not SOURCE_DIR.exists():
        print(f"Không thấy {SOURCE_DIR}")
        print("Sửa SOURCE_DIR trong scripts/import_ecomm_raw_data.py nếu data nằm chỗ khác.")
        return

    for name in ["brands", "category", "date", "products"]:
        copy_full(name)

    copy_order_items()
    copy_customers_filtered()

    print()
    print(f"Xong. Data nằm ở: {DEST_DIR}")


if __name__ == "__main__":
    main()
