"""AT04 – TC089 – XSS lưu trong bình luận phải hiển thị dạng văn bản, không chạy script."""
import uuid

import pytest
from playwright.sync_api import Page, expect

from conftest import url

PAYLOADS = [
    "<script>alert(1)</script>",
    "<img src=x onerror=alert(1)>",
]


@pytest.mark.parametrize("payload", PAYLOADS)
def test_comment_xss_is_escaped(page: Page, logged_in_user: dict, payload: str):
    dialogs = []
    page.on("dialog", lambda d: (dialogs.append(d.message), d.dismiss()))

    # Mở chi tiết bot đầu tiên ở trang chủ
    page.goto(url("index.php"))
    card = page.locator(".bot-card").first      # thẻ bot dùng onclick, không phải thẻ <a>
    expect(card).to_be_visible()
    card.click()
    page.wait_for_url("**/bot_detail.php?id=*")

    marker = uuid.uuid4().hex[:6]
    page.fill("textarea[name='content']", f"{payload}{marker}")
    page.locator("button[name='submit_comment']").click()
    page.wait_for_load_state("networkidle")

    comment = page.locator(".comment-text", has_text=marker).first
    expect(comment).to_be_visible()
    # Hiển thị nguyên văn (đã escape), không sinh thẻ HTML thật
    expect(comment).to_contain_text(payload)
    assert comment.locator("script, img").count() == 0, "Payload bị render thành thẻ HTML"
    assert not dialogs, f"Script đã chạy (alert: {dialogs})"
