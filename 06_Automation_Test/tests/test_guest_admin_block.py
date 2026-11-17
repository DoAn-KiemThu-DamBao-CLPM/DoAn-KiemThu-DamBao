"""AT03 – TC014 – Guest (chưa đăng nhập) vào các trang Admin => bị chặn, không lộ dữ liệu."""
import pytest
from playwright.sync_api import Page

from conftest import url

ADMIN_PAGES = [
    "admin_bots.php",
    "admin_stats.php",
    "admin_community.php",
    "admin_groups.php",
    "admin_add_bot.php",
]

# Tên field của các form quản trị – nếu xuất hiện nghĩa là giao diện admin bị lộ cho guest
ADMIN_FORM_MARKERS = [
    "name=\"update_commission\"", "name=\"add_theme\"", "name=\"create_group\"",
    "name=\"moderate_id\"", "name=\"is_pinned\"",
]


@pytest.mark.parametrize("page_name", ADMIN_PAGES)
def test_guest_cannot_open_admin_page(page: Page, page_name: str):
    resp = page.goto(url(f"pages/{page_name}"))
    body = page.content()
    final_path = page.url.split("?")[0]

    blocked = (
        resp.status in (401, 403)                      # bị chặn bằng mã lỗi
        or "Access Denied" in body                     # hoặc hiện thông báo từ chối
        or not final_path.endswith(page_name)          # hoặc bị chuyển hướng đi nơi khác
    )
    print(f"[{page_name}] status={resp.status} final_url={page.url}")
    assert blocked, f"Guest vào được {page_name}"
    for marker in ADMIN_FORM_MARKERS:
        assert marker not in body, f"{page_name} lộ giao diện admin ({marker})"
