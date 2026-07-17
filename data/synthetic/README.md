# Artifact synthetic đã ngừng dùng

Các CSV trong thư mục này là artifact scaffold cũ. Chúng **không phải input, fixture, evidence, slide hoặc video** của MVP sau quyết định chuyển sang EPU reference; không thêm hoặc regenerate dữ liệu tại đây.

M05/M06 sẽ thay thế đường dữ liệu bằng export EPU đã được data owner phê duyệt, pseudonymize và validate theo [hợp đồng tích hợp](../../docs/04-engineering/04-epu-data-integration-contract.md). Raw EPU/reference, mapping `MSSV`, PII và token crawl không được commit vào `data/`.

Cho đến khi handoff đó hoàn tất, consumer phải trả `insufficient_data` thay vì đọc CSV synthetic cũ.
