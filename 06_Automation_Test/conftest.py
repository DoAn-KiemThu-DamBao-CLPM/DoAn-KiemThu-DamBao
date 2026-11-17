"""Cấu hình chung + hàm dùng chung cho 6 script automation (Playwright + PyTest).

Biến môi trường (tuỳ chọn):
    ANYN_BASE_URL   mặc định http://localhost/anyn   (XAMPP: htdocs/anyn)
"""
import os
import shutil
import subprocess
import uuid

import pytest
from playwright.sync_api import Page, expect

BASE_URL = os.getenv("ANYN_BASE_URL", "http://localhost/anyn").rstrip("/")
PASSWORD = "Test1234x"          # >= 8 ký tự, có chữ + số (đúng luật validatePassword)


MYSQL_BIN = os.getenv("ANYN_MYSQL_BIN", r"C:\xampp\mysql\bin\mysql.exe")
DB_NAME = os.getenv("ANYN_DB_NAME", "anyn")


@pytest.fixture(scope="session", autouse=True)
def reset_login_throttle():
    """Web khoá đăng nhập theo IP (20 lần sai / 15 phút). AT02 cố ý đăng nhập sai nên
    sau vài lần chạy cả IP 127.0.0.1 bị khoá và các test cần đăng nhập sẽ Fail oan.
    => xoá bảng login_attempts trước mỗi lần chạy (chỉ là dọn dữ liệu test).
    Không tìm thấy mysql.exe thì bỏ qua (xoá tay trong phpMyAdmin)."""
    exe = MYSQL_BIN if os.path.exists(MYSQL_BIN) else shutil.which("mysql")
    if exe:
        subprocess.run([exe, "-u", "root", DB_NAME, "-e", "DELETE FROM login_attempts"],
                       capture_output=True)
    yield


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
