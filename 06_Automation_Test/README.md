# 06_Automation_Test – ANYN (Playwright + PyTest)

Người thực hiện: Võ Trường Hải · 6 script tự động, mỗi script chạy 3 lần.

| AT ID | TC ID | Nội dung | File script |
|---|---|---|---|
| AT01 | TC004 | Đăng nhập đúng | tests/test_login_success.py |
| AT02 | TC006 | Sai 5 lần liên tiếp → lần 6 bị khoá | tests/test_login_lockout.py |
| AT03 | TC014 | Guest vào 5 trang admin bị chặn | tests/test_guest_admin_block.py |
| AT04 | TC089 | XSS trong bình luận (2 payload) | tests/test_comment_xss.py |
| AT05 | TC036 | Gửi idea hợp lệ, nhận gem | tests/test_submit_idea.py |
| AT06 | TC064 | Mua khi không đủ gem | tests/test_shop_insufficient_gems.py |

## 1. Chuẩn bị
1. Bật **Apache + MySQL** trong XAMPP, import `source/anyn.sql`, copy thư mục `anyn` vào `C:\xampp\htdocs\anyn`.
   Kiểm tra mở được http://localhost/anyn/index.php và trang chủ có ít nhất 1 bot (AT04 cần).
2. Cài thư viện (Python 3.9+):
   ```
   pip install -r requirements.txt
   playwright install chromium
   ```
3. Nếu web không ở `http://localhost/anyn`, đặt biến môi trường (CMD: `set ANYN_BASE_URL=http://localhost:8080/anyn`).

Không cần biết mật khẩu tài khoản có sẵn: mỗi test tự đăng ký 1 tài khoản mới (`at_xxxx@mail.com`, 0 gem) qua giao diện.

## 2. Chạy
- Chạy 1 script, xem trình duyệt: `python -m pytest tests/test_login_success.py --headed          # AT01`
- `python -m pytest tests/test_login_lockout.py --headed          # AT02`
- `python -m pytest tests/test_guest_admin_block.py --headed      # AT03`
- `python -m pytest tests/test_comment_xss.py --headed            # AT04`
- `python -m pytest tests/test_submit_idea.py --headed            # AT05`
- `python -m pytest tests/test_shop_insufficient_gems.py --headed # AT06`
- Chạy cả 6 script: `pytest`
- **Chạy mỗi script 3 lần và xuất kết quả (khuyên dùng):** `python run_3_times.py`
  → tạo `evidence/results.csv` (Lần 1/2/3, thời gian TB, ngày chạy) để điền sheet **Automation**.

## 3. Bằng chứng / video
Playwright tự quay **video** và chụp **ảnh** mỗi test vào `evidence/artifacts/` (file `.webm`, `.png`);
log từng lần chạy ở `evidence/ATxx_runN.log`. Dùng các video này làm demo khi bảo vệ.
