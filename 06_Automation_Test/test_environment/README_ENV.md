# test_environment – môi trường kiểm thử dựng lại được

## Vì sao cần
Mã nguồn Anyn chạy trên PHP + MySQL (XAMPP). Bàn thử dùng để thực thi chiến dịch kiểm thử không có MySQL, nên có thêm một **lớp tương thích** để chạy *nguyên văn mã ứng dụng* trên SQLite. Chỉ một dòng trong `config/database.php` bị thay (kết nối PDO); logic nghiệp vụ không đổi.

## Thành phần
| Tệp | Vai trò |
|---|---|
| `shim/MysqlOnSqlitePDO.php` | Lớp `PDO` dịch tập con cú pháp MySQL mà ứng dụng dùng (NOW(), ON DUPLICATE KEY UPDATE, INSERT IGNORE, information_schema…) sang SQLite; **mô phỏng strict mode** (giới hạn VARCHAR/ENUM bằng CHECK) và **collation không phân biệt hoa/thường**; ghi nhật ký số truy vấn mỗi request (`ANYN_QLOG`). |
| `schema/base_schema_mysql.sql` | Lược đồ cơ sở **dựng lại** từ các câu SQL trong mã nguồn (gói nguồn thiếu CREATE TABLE của bảng lõi – giả định A-01). Dùng được trực tiếp trong phpMyAdmin: `CREATE DATABASE anyn; USE anyn;` rồi nạp tệp. |
| `tools/env.sh` | Biến môi trường (đường dẫn, cổng 8765, mật khẩu mẫu). |
| `tools/build_sut.sh` | Sao chép mã nguồn sang thư mục chạy và thay dòng kết nối CSDL. |
| `tools/init_db.php` | Tạo CSDL SQLite từ lược đồ. |
| `tools/seed.py` | Dữ liệu mẫu **xác định** (`random.seed`): 4 tài khoản (anyn_admin, alice_qa, bob_qa, carol_premium), 40 nhân vật, 12 tranh gallery, 4 bài cộng đồng, 2 ý tưởng; `--big`: 400 nhân vật, 5.012 gallery, 2.004 bài cộng đồng, 3.004 bình luận, 502 ý tưởng. |
| `tools/start_server.sh` | Khởi động `php -S` (4 worker) với cấu hình giống XAMPP mặc định (upload 40M, display_errors bật). |
| `tools/reset_env.sh` | Dựng lại toàn bộ: SUT → DB → seed pha 1 → khởi động → gọi các trang để ứng dụng tự di trú lược đồ → seed pha 2. |
| `patches/database_php_sqlite_shim.patch` | Diff duy nhất áp lên mã gốc để dựng bàn thử (chỉ `config/database.php`). |
| `patches/per_bug/BUG-0xx_*.patch` | 17 bản vá lỗi, mỗi tệp độc lập. |
| `patches/fixes.py` | `python3 fixes.py apply <anyn_gốc> <anyn_đích> [BUG-001 …]` dựng bản đã vá; `diffs <anyn_gốc> <thư_mục_ra>` sinh lại các tệp .patch. |

## Chạy trên MySQL thật (XAMPP)
1. Nạp `schema/base_schema_mysql.sql` vào CSDL `anyn`, trỏ `config/database.php` tới đó như hướng dẫn gốc.
2. `framework/db.py` đang dùng `sqlite3` để chuẩn bị dữ liệu và kiểm tra tác dụng phụ: thay `connect()` bằng kết nối `pymysql` tới cùng CSDL (các hàm `q/one/scalar/run` giữ nguyên giao diện). Đặt `ANYN_BASE_URL=http://localhost/` nếu cần.
3. Các test về nhật ký truy vấn (NF-PERF-04) và tải tệp `.htaccess` (NF-SEC-10) cần điều chỉnh tương ứng (không có `ANYN_QLOG` trên MySQL; trên Apache NF-SEC-10 chạy được đầy đủ).
