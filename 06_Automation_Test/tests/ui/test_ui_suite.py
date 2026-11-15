"""Browser-level (Playwright / Chromium) automated cases.  Each one re-checks through the real UI a case that is
specified and executed at HTTP level in tests/functional (see `implements`)."""
import re

from framework import db, images
from framework.client import AnynClient, uniq
from framework.config import ADMIN, ALICE, BASE_URL, PAGES, SEED_PASSWORD
from framework.tcmeta import ui_case

from .conftest import ui_login


@ui_case("UI-01", "TC-REG-01", "Đăng ký tài khoản qua form trên trình duyệt",
         ["Mở register.php", "Điền username/email/password/confirm", "Bấm 'Create Account'"],
         "Hiện hộp 'Account created! You can now sign in.' kèm liên kết Sign in; bản ghi users được tạo")
def test_ui_01(new_page, shot, ev):
    pg = new_page()
    name = uniq("ui")
    pg.goto(PAGES + "/register.php")
    pg.fill("input[name=username]", name)
    pg.fill("input[name=email]", f"{name}@qa.test")
    pg.fill("input[name=password]", "Passw0rd!x")
    pg.fill("input[name=password_confirm]", "Passw0rd!x")
    pg.click("button.btn-submit")
    pg.wait_for_selector(".success-box")
    shot(pg, "UI-01_register_success")
    txt = pg.inner_text(".success-box")
    ev.note(f"success box: {txt.strip()[:80]}")
    assert "Account created" in txt and db.one("SELECT id FROM users WHERE username=?", (name,))


@ui_case("UI-02", "TC-LOG-01", "Đăng nhập thành công / sai mật khẩu và đăng xuất trên giao diện",
         ["Đăng nhập sai mật khẩu", "Đăng nhập đúng", "Mở menu và Logout"],
         "Sai: hiện 'Invalid email or password.' và ở lại trang login; đúng: về trang chủ, thấy username; sau Logout không còn truy cập được profile.php")
def test_ui_02(new_page, shot, ev):
    pg = new_page()
    ui_login(pg, ALICE["email"], "Wrong#9999")
    shot(pg, "UI-02_login_invalid")
    err = pg.inner_text(".error-box")
    ev.note(f"sai mật khẩu → {err.strip()}")
    assert "Invalid email or password" in err and "login.php" in pg.url
    ev.note(f"ô email sau khi đăng nhập sai: {pg.input_value('input[name=email]')!r}")
    pg.fill("input[name=email]", ALICE["email"])
    pg.fill("input[name=password]", SEED_PASSWORD)
    pg.click("button[type=submit]")
    pg.wait_for_load_state()
    shot(pg, "UI-02_login_ok")
    ev.note(f"sau đăng nhập đúng URL = {pg.url}")
    assert pg.url.rstrip("/").endswith("index.php") and "alice_qa" in pg.content()
    pg.goto(PAGES + "/logout.php")
    pg.goto(PAGES + "/profile.php")
    assert "login.php" in pg.url, "sau khi đăng xuất vẫn vào được profile"


@ui_case("UI-03", "TC-BRW-02", "Tìm kiếm bằng ô Search ở trang chủ",
         ["Gõ 'nightblade' vào ô tìm kiếm", "Nhấn Enter"], "Danh sách chỉ gồm các nhân vật có chữ Nightblade; số thẻ khớp DB (≤ 24); ô tìm kiếm giữ lại từ khoá")
def test_ui_03(new_page, shot, ev):
    pg = new_page()
    pg.goto(BASE_URL + "/anyn/index.php")
    pg.fill("#searchInput", "nightblade")
    pg.press("#searchInput", "Enter")
    pg.wait_for_load_state()
    cards = pg.locator("[onclick*='bot_detail.php?id=']").count()
    expect = min(24, db.scalar("SELECT COUNT(*) FROM bots WHERE name LIKE '%nightblade%' OR description LIKE '%nightblade%'"))
    shot(pg, "UI-03_search")
    ev.note(f"UI hiển thị {cards} thẻ, DB kỳ vọng {expect}; giá trị ô tìm kiếm = {pg.input_value('#searchInput')!r}")
    assert cards == expect and pg.input_value("#searchInput") == "nightblade"


@ui_case("UI-04", "TC-RAT-01", "Chấm điểm 4 sao bằng cách bấm sao trên trang chi tiết nhân vật",
         ["Đăng nhập tài khoản mới", "Mở bot_detail.php?id=31", "Bấm sao thứ 4", "Bấm nút gửi đánh giá"],
         "Có 1 bản ghi ratings score=4 cho user; điểm trung bình của bot = 4.00")
def test_ui_04(new_page, shot, ev):
    u = AnynClient.new_user("uir")
    db.run("DELETE FROM ratings WHERE bot_id=31")
    pg = new_page()
    ui_login(pg, u.email, u.password)
    pg.goto(PAGES + "/bot_detail.php?id=31")
    pg.click("label[for=star4]")
    pg.click("form:has(.star-picker) button[type=submit]")
    pg.wait_for_load_state()
    shot(pg, "UI-04_rating")
    row = db.one("SELECT score FROM ratings WHERE bot_id=31 AND user_id=?", (u.user_id,))
    avg = db.scalar("SELECT total_rating FROM bots WHERE id=31")
    ev.note(f"ratings row={row}, bots.total_rating={avg}")
    assert row and row["score"] == 4 and float(avg) == 4.0


@ui_case("UI-05", "TC-CMT-01", "Đăng bình luận (tiếng Việt + emoji) qua form",
         ["Đăng nhập", "Mở bot_detail.php?id=32", "Nhập bình luận", "Bấm 'Post Comment'"], "Bình luận hiển thị trong danh sách với username; lưu UTF-8 đúng")
def test_ui_05(new_page, shot, ev):
    u = AnynClient.new_user("uic")
    pg = new_page()
    ui_login(pg, u.email, u.password)
    pg.goto(PAGES + "/bot_detail.php?id=32")
    text = "Nhân vật rất hay! 😍"
    pg.fill("textarea[name=content]", text)
    pg.click("button[name=submit_comment]")
    pg.wait_for_load_state()
    shot(pg, "UI-05_comment")
    body = pg.inner_text("body")
    ev.note(f"comment visible={text in body}, username visible={u.username in body}")
    assert text in body and u.username in body


@ui_case("UI-06", "TC-GAL-02", "Bấm nút reaction trên Official Gallery rồi bấm lại để gỡ",
         ["Đăng nhập", "Mở gallery.php", "Bấm 👍 của ảnh đầu tiên", "Bấm lần nữa"], "Lần 1: số reaction của nút tăng 1; lần 2: trở về đúng giá trị ban đầu (so sánh tương đối, không phụ thuộc dữ liệu do test khác tạo)")
def test_ui_06(new_page, shot, ev):
    u = AnynClient.new_user("uig")
    pg = new_page()
    ui_login(pg, u.email, u.password)
    pg.goto(PAGES + "/gallery.php")
    btn = pg.locator(".btn-react.react-like").first
    before = btn.inner_text()
    btn.click()
    pg.wait_for_load_state()
    after = pg.locator(".btn-react.react-like").first.inner_text()
    shot(pg, "UI-06_reaction_on")
    ev.note(f"nút like: '{before}' → '{after}'")
    count = lambda text: int("".join(ch for ch in text if ch.isdigit()) or 0)   # "👍 3" -> 3
    assert count(after) == count(before) + 1, f"lần 1: {before!r} -> {after!r}"
    pg.locator(".btn-react.react-like").first.click()
    pg.wait_for_load_state()
    back = pg.locator(".btn-react.react-like").first.inner_text()
    ev.note(f"bấm lần 2 (gỡ reaction): '{after}' → '{back}'")
    assert count(back) == count(before), f"lần 2: {after!r} -> {back!r}"


@ui_case("UI-07", "TC-ADM-08", "Admin thêm nhân vật bằng trang admin_add_bot.php (bấm nút 'XÁC NHẬN THÊM BOT')",
         ["Đăng nhập admin", "Mở admin_add_bot.php", "Điền tên, mô tả, chọn ảnh", "Bấm 'XÁC NHẬN THÊM BOT'"],
         "Bot được tạo và hiện thông báo thành công; không có trang 'Security Error' (HTTP 403)", bug=["BUG-016"])
def test_ui_07(new_page, shot, ev, tmp_path):
    pg = new_page()
    ui_login(pg, ADMIN["email"], ADMIN["password"])
    pg.goto(PAGES + "/admin_add_bot.php")
    f = tmp_path / "b.png"
    f.write_bytes(images.png(size=(64, 64)))
    name = uniq("UIBot")
    pg.fill("input[name=name]", name)
    pg.fill("textarea[name=description]", "added through the page")
    pg.set_input_files("input[name=bot_image]", str(f))
    with pg.expect_response(lambda r: "admin_add_bot" in r.url and r.request.method == "POST") as info:
        pg.click("text=XÁC NHẬN THÊM BOT")
    status = info.value.status
    pg.wait_for_load_state()
    shot(pg, "UI-07_admin_add_bot")
    bot = db.one("SELECT id FROM bots WHERE name=?", (name,))
    if bot:
        db.run("DELETE FROM bot_themes WHERE bot_id=?", (bot["id"],))
        db.run("DELETE FROM bots WHERE id=?", (bot["id"],))
    ev.note(f"POST → HTTP {status}; trang kết quả: {pg.inner_text('body')[:90]!r}; bot tạo ra={bool(bot)}")
    assert status != 403 and bot, f"bấm nút trả HTTP {status}: 'Invalid or expired security token' — không thể thêm bot qua trang này"


@ui_case("UI-08", "NF-USA-01", "Giao diện responsive ở viewport điện thoại 375×812: không tràn ngang, menu hamburger mở được",
         ["Mở trang chủ ở 375×812", "Đo scrollWidth", "Bấm hamburger"], "document.scrollWidth ≤ 375 (không cuộn ngang); sidebar hiện ra sau khi bấm hamburger")
def test_ui_08(new_page, shot, ev):
    pg = new_page(viewport=(375, 812))
    for path in ("/anyn/index.php", "/anyn/pages/login.php", "/anyn/pages/register.php", "/anyn/pages/gallery.php"):
        pg.goto(BASE_URL + path)
        w = pg.evaluate("document.documentElement.scrollWidth")
        ev.note(f"{path}: scrollWidth={w}")
        assert w <= 376, f"{path} tràn ngang ({w}px)"
    pg.goto(BASE_URL + "/anyn/index.php")
    pg.click("#hamburger")
    pg.wait_for_timeout(500)
    shot(pg, "UI-08_mobile_menu")
    box = pg.locator("#sidebar").bounding_box()
    ev.note(f"sidebar bbox sau khi bấm hamburger = {box}")
    assert box and box["x"] > -50, "sidebar không hiện sau khi bấm hamburger"


@ui_case("UI-09", "NF-USA-02", "Chế độ tối (dark mode) được áp dụng và ghi nhớ sau khi tải lại trang",
         ["Mở trang chủ", "Bấm nút đổi giao diện", "Tải lại trang"], "Thuộc tính data-theme đổi sang dark và vẫn giữ sau khi reload")
def test_ui_09(new_page, shot, ev):
    pg = new_page()
    pg.goto(BASE_URL + "/anyn/index.php")
    first = pg.evaluate("document.documentElement.getAttribute('data-theme')")
    pg.click("#themeBtn")
    pg.wait_for_timeout(300)
    after = pg.evaluate("document.documentElement.getAttribute('data-theme')")
    pg.reload()
    kept = pg.evaluate("document.documentElement.getAttribute('data-theme')")
    shot(pg, "UI-09_dark_mode")
    ev.note(f"data-theme: ban đầu={first!r} → sau bấm={after!r} → sau reload={kept!r}")
    assert after != first and kept == after
