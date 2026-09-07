# Bài 5 — Git Folder (Databricks Repos) vs Bundle deploy

## Mục tiêu
Không nhầm lẫn 2 luồng đưa code lên workspace — và biết khi nào (nếu có)
mới cần Git Folder.

## Nội dung

| | **Bundle deploy** (đang dùng) | **Git Folder / Repos** |
|---|---|---|
| Code ở đâu | Local (VS Code) | Trực tiếp trên browser, trong workspace |
| Đưa code lên workspace | `databricks bundle deploy` | Databricks tự `git clone` khi "Add Git Folder" |
| Vị trí trên workspace | `/Workspace/.../.bundle/<project>/<target>/files` — **tự sinh, bị ghi đè mỗi lần deploy** | `/Workspace/Users/.../<repo_name>` — bản clone thật, sửa tay ở đây |
| Commit/push GitHub từ đâu | Từ máy bạn (terminal) | Từ nút Commit/Push trong UI |
| Cần connect GitHub bằng token? | Không | Có, bắt buộc |

### Khi GitHub đã là single source of truth + có CI/CD

Nếu CI/CD đã tự `bundle deploy` sau mỗi merge, **Git Folder gần như không
cần thiết** — nó tạo ra 1 đường đi code thứ 2, song song với CI/CD, dễ gây
lệch code nếu ai đó sửa/push thẳng trong Git Folder, bỏ qua PR review.

Git Folder chỉ thật sự hữu ích cho:
- Người không dùng CLI/git terminal (data analyst) muốn version-control qua UI.
- Debug tương tác nhanh trên cluster thật — sandbox thử nghiệm, không phải
  nơi deploy chính thức; logic cuối vẫn phải đưa qua PR/CI như bình thường.

## Áp dụng vào project

Với hướng đi hiện tại (bundle + CLI + sau này CI/CD), **không cần** Add Git
Folder. Toàn bộ workflow deploy trong [../../setup.md](../../setup.md)
không đụng tới Git Folder ở bất kỳ bước nào.
