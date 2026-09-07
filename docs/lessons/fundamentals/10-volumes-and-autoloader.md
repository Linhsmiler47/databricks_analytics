# Bài 10 — Từ file thô tới Delta table: Volume & Auto Loader

## Mục tiêu
Hiểu tại sao pipeline không đọc thẳng file CSV, mà phải qua 2 bước trung
gian: **Volume** rồi mới tới **Bronze table**. Đây là câu hỏi rất đúng chỗ
— nhìn qua tưởng thừa bước, nhưng mỗi bước giải quyết 1 vấn đề cụ thể.

## 3 chặng, 3 lý do khác nhau

```
CSV thô (file)  →  Volume  →  Bronze table (Delta)  →  Silver/Gold
```

### Chặng 1 → 2: vì sao file phải nằm trong Volume, không phải ở "đâu đó"?

**Volume** là object của Unity Catalog dùng để quản lý **file** (không phải
bảng) — cùng namespace `catalog.schema.volume_name` như table (xem
[Bài 4 — Unity Catalog](04-unity-catalog.md)). Nếu không có Volume, file
CSV nằm ở 1 chỗ nào đó không ai quản lý quyền, không track được ai đọc/ghi,
không hiện trong Catalog Explorer.

→ Volume = **"hộp thư đến" có governance**, để file thô cũng được Unity
Catalog quản lý quyền/audit y hệt table, trước khi nó được xử lý thành gì
đó.

### Chặng 2 → 3: vì sao phải convert thành Bronze table, không đọc thẳng CSV mỗi lần?

3 lý do, mỗi lý do ứng với 1 giới hạn thật của CSV thô:

| Vấn đề của CSV thô | Delta table (Bronze) giải quyết bằng |
|---|---|
| Không có transaction — đọc giữa lúc ghi có thể bị lỗi/thiếu dòng | ACID transaction (xem [Bài 3 — Delta Lake](03-delta-lake.md)) |
| Đọc lại **toàn bộ** file mỗi lần, kể cả file cũ đã xử lý rồi → chậm dần theo thời gian | **Auto Loader** (`cloudFiles`) tự nhớ file nào đã xử lý (qua checkpoint), lần sau chỉ đọc file **mới** |
| Không có schema cố định, không time travel, không query nhanh bằng SQL chuẩn | Delta format = Parquet + transaction log, có schema, có version history |

Đây chính là lý do bài tập 1.4 yêu cầu bạn upload `v2.csv` (snapshot thứ 2)
rồi chạy lại pipeline: Bronze table có thêm dòng của `v2`, **không đọc lại
`v1.csv`** — vì Auto Loader lưu checkpoint "đã xử lý file nào", không phải
vì Spark "thông minh" tự đoán. Nếu bạn dùng `spark.read.csv()` thường
(không phải Auto Loader), nó sẽ đọc lại **toàn bộ** thư mục mỗi lần —
không incremental.

## Bonus: 2 kiểu CDC khác nhau (liên quan tới bài 1.5)

Auto Loader chỉ lo việc đưa file vào Bronze. Việc suy ra INSERT/UPDATE/
DELETE ở tầng Silver có 2 cách tiếp cận khác hẳn nhau:

- **Operation-log CDC** (`create_auto_cdc_flow`): nguồn đã có sẵn cột
  `operation` (INSERT/UPDATE/DELETE) — kiểu Debezium/Fivetran xuất ra.
- **Snapshot-diff CDC** (`create_auto_cdc_from_snapshot_flow`): nguồn chỉ
  là các bản chụp "trạng thái đầy đủ" tại nhiều thời điểm — Lakeflow tự so
  sánh 2 bản chụp liền nhau theo `keys` để suy ra thay đổi, không cần cột
  operation nào. Đây là cách case study trong repo dùng (bạn tự sửa tay
  `customers.csv`, mỗi lần "chốt" là 1 snapshot mới) — mô phỏng đúng thực
  tế thường gặp hơn: hệ thống nguồn (ERP, Excel export...) thường chỉ xuất
  ra được "trạng thái hiện tại", không tự sinh log thay đổi.

## Ghép lại toàn bộ lý do

```
CSV thô                     Volume                      Bronze table
(chỉ là file, ai cũng   →   (Unity Catalog quản lý  →   (Delta: ACID +
đọc/ghi tùy ý, không        quyền, giống 1 "ngăn         schema + Auto Loader
version, không quyền)       kéo" có khóa)                nhớ đã xử lý gì)
```

Không bước nào "thừa" — Volume giải quyết vấn đề **governance**, Bronze
table (qua Auto Loader) giải quyết vấn đề **hiệu năng + độ tin cậy khi dữ
liệu tăng dần theo thời gian**.

## Áp dụng vào project

- [roadmap/phase-1-track1-cdc-demo.md mục 1.4](../../roadmap/phase-1-track1-cdc-demo.md) —
  đúng 3 chặng này bằng code thật (`CREATE VOLUME` → `databricks fs cp` →
  `@dp.table` + `cloudFiles`).
- Liên hệ [operations/02-asset-bundles-fundamentals.md](../operations/02-asset-bundles-fundamentals.md) —
  phần "Auto Loader không phải tính năng của bundle" giải thích rõ hơn ranh
  giới giữa deploy-time (bundle) và run-time (Auto Loader tự detect file).
