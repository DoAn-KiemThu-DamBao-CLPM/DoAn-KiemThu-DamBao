# 06_Automation_Test – bộ kiểm thử tự động Anyn

Thư mục này chứa **toàn bộ mã kiểm thử tự động, môi trường dựng lại được và kết quả thực thi** của dự án. Mọi con số trong các báo cáo 04, 05, 07, 08 đều đến từ các tệp JSON trong `results/` – chạy lại bằng các lệnh dưới đây sẽ cho kết quả tương đương.

## 1. Cấu trúc

| Đường dẫn | Nội dung |
|---|---|
| `tests/functional/test_ts01…ts11_*.py` | 94 test case chức năng (HTTP). Mỗi hàm test mang đặc tả test case trong decorator `@tc(...)` → bảng 03_Test_Scenario_Test_Case.xlsx sinh ra từ chính các decorator này. |
| `tests/ui/test_ui_suite.py` | 9 kịch bản giao diện (Playwright + Chromium), ảnh chụp lưu ở `results/<vòng>/screenshots/`. |
| `tests/security/test_security.py` | 11 test case bảo mật (NF-SEC-01…11). |
| `nonfunctional/performance/test_performance.py` | 4 test case hiệu năng (NF-PERF-01…04), chạy với dữ liệu nhỏ và lớn. |
| `framework/` | `client.py` (máy khách HTTP như trình duyệt: cookie + CSRF), `db.py` (truy cập CSDL để chuẩn bị dữ liệu và kiểm tra tác dụng phụ), `tcmeta.py` (đăng ký đặc tả test case), `reporter.py` (plugin pytest ghi JSON kết quả + bằng chứng), `config.py`. |
| `conftest.py`, `pytest.ini` | Fixture (`guest`, `user`, `user2`, `premium`, `admin`, `alice`, `bob`) và cấu hình pytest. |
| `test_environment/` | Môi trường dựng lại được: lớp tương thích MySQL→SQLite, lược đồ cơ sở dựng lại, dữ liệu mẫu, script dựng/khởi động, **các bản vá lỗi** (xem `test_environment/README_ENV.md`). |
| `results/cycle1/`, `results/cycle2/` | Kết quả thô: `execution_results.json`, `ui_results.json`, `nonfunctional_results.json`, `perf_small.json`, `perf_big.json`, `screenshots/`. |
| `run_cycle.sh`, `envrc.sh` | Chạy một vòng kiểm thử hoàn chỉnh. |

## 2. Yêu cầu

* Linux/macOS (hoặc WSL), `bash`, `curl`, `php` ≥ 8.1 (có `pdo_sqlite`), Python ≥ 3.10.
* `pip install -r requirements.txt` rồi `playwright install chromium` (chỉ cần cho 9 kịch bản UI).
* Mã nguồn gốc: giải nén `anyn_updated_1.zip`, thư mục chứa `index.php` là **ANYN_SRC**.

## 3. Chạy lại

```bash
cd 06_Automation_Test
export ANYN_SRC=/đường/dẫn/tới/anyn            # mã nguồn GỐC
source ./envrc.sh

# Vòng 1 – bản gốc (kỳ vọng: 78/94 chức năng Pass, 16 Fail)
./run_cycle.sh cycle1 "$ANYN_SRC" /tmp/ket_qua_lai

# Vòng 2 – bản đã vá (kỳ vọng: 93/94 chức năng Pass; còn lại BUG-013 chủ động hoãn)
python3 test_environment/patches/fixes.py apply "$ANYN_SRC" /tmp/anyn_fixed/anyn
./run_cycle.sh cycle2 /tmp/anyn_fixed/anyn /tmp/ket_qua_lai
```

Tham số thứ ba của `run_cycle.sh` là thư mục gốc ghi kết quả (mặc định `./results`; **thư mục `<vòng>` bên trong bị xoá trước khi chạy**). Chạy từng phần thủ công:

```bash
test_environment/tools/reset_env.sh "$ANYN_SRC"            # dựng môi trường sạch + dữ liệu nhỏ
QA_CYCLE=cycle1 python3 -m pytest tests -q                  # chức năng + bảo mật + UI
QA_CYCLE=cycle1 python3 -m pytest tests -q -k test_com_   # ví dụ: chỉ nhóm Commission (hàm test_com_01…)
test_environment/tools/reset_env.sh "$ANYN_SRC" --big       # dữ liệu lớn (5.012 ảnh gallery…)
QA_CYCLE=cycle1 python3 -m pytest nonfunctional -q
```

Sau khi chạy xong có thể mở lại ứng dụng đang chạy tại `http://127.0.0.1:8765/anyn/` (mật khẩu tài khoản mẫu: `User@12345`, **chỉ dùng cho bàn thử**).

## 4. Đọc kết quả

Mỗi bản ghi trong `execution_results.json` có: `id` (mã TC), `status` (Pass/Fail/Blocked), `actual` (thông báo khi Fail), `duration` (giây), `evidence[]` (các dòng ghi nhận tự động: mã HTTP, nội dung, trạng thái CSDL), `screens[]`, `executed_at` (UTC), `bug[]`.

## 5. Giới hạn cần biết

1. CSDL là **SQLite** qua lớp tương thích (MySQL không có trong bàn thử) → kết quả liên quan khoá hàng/đồng thời/strict-mode cần xác nhận lại trên MySQL thật.
2. Máy chủ PHP **built-in** bỏ qua `.htaccess` → NF-SEC-10 chỉ kiểm tra tĩnh (Blocked ở vòng 2).
3. Số đo thời gian (ms) chỉ mang tính chỉ báo (máy chủ loopback, không có độ trễ mạng).
4. Lược đồ gốc của các bảng lõi không có trong gói nguồn → được dựng lại (giả định A-01, xem Test Plan).
