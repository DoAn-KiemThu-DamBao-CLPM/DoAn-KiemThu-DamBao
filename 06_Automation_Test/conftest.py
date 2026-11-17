"""Cấu hình chung + hàm dùng chung cho 6 script automation (Playwright + PyTest).

Biến môi trường (tuỳ chọn):
    ANYN_BASE_URL   mặc định http://localhost/anyn   (XAMPP: htdocs/anyn)
    ANYN_MYSQL_BIN  mặc định C:\\xampp\\mysql\\bin\\mysql.exe
    ANYN_DB_NAME    mặc định anyn
"""
import os
import shutil
import subprocess
import uuid
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

BASE_URL = os.getenv("ANYN_BASE_URL", "http://localhost/anyn").rstrip("/")
PASSWORD = "Test1234x"          # >= 8 ký tự, có chữ + số (đúng luật validatePassword)


MYSQL_BIN = os.getenv("ANYN_MYSQL_BIN", r"C:\xampp\mysql\bin\mysql.exe")
DB_NAME = os.getenv("ANYN_DB_NAME", "anyn")


# ======================================================================
# 1. DỌN DỮ LIỆU TEST (gọi mysql.exe của XAMPP, nên MySQL phải đang chạy)
# ======================================================================
def _mysql(sql: str) -> None:
    """Chạy lệnh SQL bằng mysql.exe. Lỗi chỉ in cảnh báo, không làm hỏng test."""
    exe = MYSQL_BIN if os.path.exists(MYSQL_BIN) else shutil.which("mysql")
    if not exe:
        print("[db] Không tìm thấy mysql.exe, bỏ qua bước dọn dữ liệu")
        return
    # -f: gặp lỗi ở 1 câu lệnh vẫn chạy tiếp các câu còn lại
    r = subprocess.run([exe, "-u", "root", "-f", DB_NAME, "-e", sql],
                       capture_output=True, text=True)
    if r.stderr.strip():
        print(f"[db] {r.stderr.strip()}")


# Xoá toàn bộ tài khoản do test tạo (username bắt đầu bằng "at_") và dữ liệu của chúng.
# Bảng con (có khoá ngoại tới users) xoá TRƯỚC, bảng users xoá SAU CÙNG.
# Tên bảng lấy từ anyn.sql.
CLEANUP_SQL = """
DELETE FROM comments          WHERE user_id IN (SELECT id FROM users WHERE username LIKE 'at\\_%');
DELETE FROM idea_upvotes      WHERE user_id IN (SELECT id FROM users WHERE username LIKE 'at\\_%');
DELETE FROM ideas             WHERE user_id IN (SELECT id FROM users WHERE username LIKE 'at\\_%');
DELETE FROM ratings           WHERE user_id IN (SELECT id FROM users WHERE username LIKE 'at\\_%');
DELETE FROM chat_messages     WHERE user_id IN (SELECT id FROM users WHERE username LIKE 'at\\_%');
DELETE FROM commissions       WHERE user_id IN (SELECT id FROM users WHERE username LIKE 'at\\_%');
DELETE FROM gem_mission_log   WHERE user_id IN (SELECT id FROM users WHERE username LIKE 'at\\_%');
DELETE FROM user_login_logs   WHERE user_id IN (SELECT id FROM users WHERE username LIKE 'at\\_%');
DELETE FROM user_inventory    WHERE user_id IN (SELECT id FROM users WHERE username LIKE 'at\\_%');
DELETE FROM shop_purchase_log WHERE user_id IN (SELECT id FROM users WHERE username LIKE 'at\\_%');
DELETE FROM users             WHERE username LIKE 'at\\_%';
DELETE FROM login_attempts;
"""


@pytest.fixture(scope="session", autouse=True)
def reset_login_throttle():
    """Web khoá đăng nhập theo IP (20 lần sai / 15 phút). AT02 cố ý đăng nhập sai nên
    sau vài lần chạy cả IP 127.0.0.1 bị khoá và các test cần đăng nhập sẽ Fail oan.
    => xoá bảng login_attempts trước mỗi lần chạy.
    Sau khi chạy xong: dọn tài khoản/bình luận/idea do test tạo ra (CLEANUP_SQL)."""
    _mysql("DELETE FROM login_attempts")
    yield
    _mysql(CLEANUP_SQL)
    print("[cleanup] Đã chạy dọn dữ liệu test (tài khoản at_*, bình luận, idea)")


# ======================================================================
# 2. BÁO CÁO: mỗi test đã kiểm tra gì, PASS hay FAIL, vì sao fail
# ======================================================================
RESULTS = []


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call" or (rep.when == "setup" and rep.failed):
        doc = (item.function.__doc__ or "").strip().splitlines()
        reason = ""
        if call.excinfo:
            reason = call.excinfo.exconly().strip().splitlines()[0][:200]
        RESULTS.append((item.name, doc[0] if doc else "",
                        "PASS" if rep.passed else "FAIL", reason))


def pytest_terminal_summary(terminalreporter):
    if not RESULTS:
        return
    lines = ["", "===== TÓM TẮT KẾT QUẢ TEST ====="]
    for name, desc, status, reason in RESULTS:
        lines.append(f"[{status}] {name}")
        lines.append(f"        Kiểm tra: {desc}")
        if reason:
            lines.append(f"        Lý do lỗi: {reason}")
    ok = sum(1 for r in RESULTS if r[2] == "PASS")
    lines.append(f"Tổng: {ok}/{len(RESULTS)} PASS, {len(RESULTS) - ok} FAIL")
    for ln in lines:
        terminalreporter.write_line(ln)
    Path("evidence").mkdir(exist_ok=True)
    with open("evidence/summary.txt", "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


# ======================================================================
# 3. HÀM DÙNG CHUNG
# ======================================================================
def url(path: str) -> str:
    return f"{BASE_URL}/{path.lstrip('/')}"


def register(page: Page, username: str, email: str, password: str = PASSWORD) -> None:
    page.goto(url("pages/register.php"))
    page.fill("input[name='username']", username)
    page.fill("input[name='email']", email)
    page.fill("input[name='password']", password)
    page.fill("input[name='password_confirm']", password)
    page.locator("form button[type='submit']").first.click()
    expect(page.get_by_text("Account created")).to_be_visible()


def login(page: Page, email: str, password: str = PASSWORD) -> None:
    page.goto(url("pages/login.php"))
    page.fill("input[name='email']", email)
    page.fill("input[name='password']", password)
    page.locator("button.btn-submit").click()


def is_logged_in(page: Page) -> bool:
    return page.locator("a.logout-link, a[href$='logout.php']").count() > 0


@pytest.fixture()
def new_user(page: Page) -> dict:
    """Tạo 1 tài khoản mới qua giao diện (mỗi lần chạy 1 tài khoản riêng
    => không bị ảnh hưởng bởi dữ liệu / bộ đếm khoá đăng nhập của lần chạy trước)."""
    tag = uuid.uuid4().hex[:10]
    user = {"username": f"at_{tag}", "email": f"at_{tag}@mail.com", "password": PASSWORD}
    register(page, user["username"], user["email"], user["password"])
    return user


@pytest.fixture()
def logged_in_user(page: Page, new_user: dict) -> dict:
    login(page, new_user["email"], new_user["password"])
    expect(page.locator("a.logout-link, a[href$='logout.php']").first).to_be_attached()
    return new_user
