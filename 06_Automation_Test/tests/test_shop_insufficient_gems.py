"""AT06 – TC064 – Mua khi không đủ gem => báo 'Not enough gems', số gem không đổi."""
import re

from playwright.sync_api import Page, expect

from conftest import url

ITEM_KEY = "avt_gold"      # Gold Avatar Ring – 25 gem; tài khoản mới có 0 gem


def _gems(page: Page) -> int:
    txt = page.locator(".gems-balance").inner_text()
    return int(re.search(r"([\d,]+)\s*gems", txt).group(1).replace(",", ""))


def test_buy_without_enough_gems(page: Page, logged_in_user: dict):
    page.goto(url("pages/shop.php?tab=shop"))
    gems_before = _gems(page)
    assert gems_before < 25, "Tài khoản test phải có ít gem hơn giá vật phẩm"

    form = page.locator(f"form:has(input[name='buy_item'][value='{ITEM_KEY}'])")
    buy_btn = form.locator("button.btn-gem")
    # Giao diện đã khoá nút Mua; bỏ khoá để kiểm tra luôn phía server
    expect(buy_btn).to_be_disabled()
    buy_btn.evaluate("b => b.disabled = false")
    buy_btn.click()

    expect(page.get_by_text("Not enough gems")).to_be_visible()
    assert _gems(page) == gems_before, "Gem bị thay đổi dù mua thất bại"
