"""AT01 – TC004 – Đăng nhập đúng."""
from playwright.sync_api import Page, expect

from conftest import login, is_logged_in


def test_login_success(page: Page, new_user: dict):
    login(page, new_user["email"], new_user["password"])

    # Kỳ vọng: rời trang login, header hiện tên người dùng + nút Logout
    expect(page).not_to_have_url(__import__("re").compile(r"login\.php"))
    expect(page.locator(".pill-uname").first).to_have_text(new_user["username"])
    assert is_logged_in(page)
