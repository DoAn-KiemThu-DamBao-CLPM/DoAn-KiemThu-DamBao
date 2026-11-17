"""AT02 – TC006 – Sai 5 lần liên tiếp cùng email => lần 6 (dù đúng mật khẩu) bị khoá tạm thời."""
from playwright.sync_api import Page, expect

from conftest import login, is_logged_in


def test_login_lockout_after_5_failures(page: Page, new_user: dict):
    for i in range(1, 6):
        login(page, new_user["email"], "Sai_mat_khau_1")
        expect(page.get_by_text("Invalid email or password.")).to_be_visible()
        assert not is_logged_in(page), f"Lần sai thứ {i} mà vẫn đăng nhập được"

    # Lần 6: nhập ĐÚNG mật khẩu nhưng phải bị chặn
    login(page, new_user["email"], new_user["password"])
    expect(page.get_by_text("Too many failed attempts")).to_be_visible()
    assert not is_logged_in(page), "Bị khoá nhưng vẫn đăng nhập được"
