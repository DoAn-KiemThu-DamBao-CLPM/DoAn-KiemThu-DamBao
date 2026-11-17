"""AT05 – TC036 – Gửi idea hợp lệ => idea xuất hiện trong danh sách, nhận gem nhiệm vụ."""
import re
import uuid

from playwright.sync_api import Page, expect

from conftest import url


def _gems(page: Page) -> int:
    page.goto(url("pages/shop.php"))
    txt = page.locator(".gems-balance").inner_text()
    return int(re.search(r"([\d,]+)\s*gems", txt).group(1).replace(",", ""))


def test_submit_valid_idea(page: Page, logged_in_user: dict):
    gems_before = _gems(page)

    title = f"AT Idea {uuid.uuid4().hex[:6]}"
    page.goto(url("pages/submit_idea.php"))
    page.fill("input[name='title']", title)
    page.fill("textarea[name='appearance']", "Long black hair, oversized t-shirt")
    page.fill("textarea[name='context']", "A reserved kuudere who hides her emotions")
    page.locator("button.btn-submit").click()

    expect(page.locator(".alert-success")).to_contain_text("Idea submitted successfully")

    # Idea mới xuất hiện trong danh sách Idea Board
    page.goto(url("pages/ideas.php"))
    expect(page.get_by_text(title).first).to_be_visible()

    # Nhận gem nhiệm vụ "Submit an idea" (+10)
    assert _gems(page) > gems_before, "Không được cộng gem sau khi gửi idea"
