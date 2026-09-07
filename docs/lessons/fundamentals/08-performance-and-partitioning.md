# Bài 8 — Performance & Partitioning

## Mục tiêu
Đừng đào quá sâu lúc mới học — chỉ cần thuộc 7 keyword và hiểu 1 insight
cốt lõi về distributed computing.

## 7 keyword cần thuộc

`Partitioning`, `Shuffle`, `Broadcast Join`, `Caching`, `Photon`,
`OPTIMIZE`, `Query Plan`.

### Vấn đề điển hình: join bảng lớn với bảng nhỏ

```
Table A: 5 TB
Table B: 10 MB
A JOIN B
```

Có thể broadcast bảng nhỏ để tránh shuffle:
```python
from pyspark.sql.functions import broadcast

df = large_df.join(broadcast(small_df), "id")
```

Mục tiêu: **giảm shuffle → giảm network → chạy nhanh hơn.**

Với Delta, cũng thường gặp:
```sql
OPTIMIZE production.sales.orders;
```

**Insight quan trọng nhất khi phỏng vấn:** không cần thuộc mọi command,
chỉ cần hiểu — *distributed computing thường chậm khi phải di chuyển
nhiều dữ liệu giữa các worker.*

## Spark partition — concept quan trọng nhất

Ví dụ dataset 1 TB — Spark không để 1 máy xử lý hết, mà chia thành nhiều
partition, mỗi partition giao cho 1 worker:

```
DataFrame
    ↓
Partitions
    ↓
Executors / workers
```

Các operation như `groupBy`, `join`, `distinct`, `orderBy` thường gây
**shuffle** — dữ liệu phải được redistribute giữa các máy. Shuffle nhiều
→ thường chậm.

## Áp dụng vào project

Data mẫu hiện tại (`samples.nyctaxi.trips`, vài nghìn dòng) quá nhỏ để
thấy shuffle/broadcast join có ý nghĩa — đây là kiến thức nên nhớ trước,
áp dụng thật khi làm việc với dataset lớn hơn (không nằm trong scope
Phase 1 của repo này).
