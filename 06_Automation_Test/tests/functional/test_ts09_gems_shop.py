"""TS-09 — Gem economy: daily missions, shop purchases, vouchers, image-set requests (FR-09)."""
import concurrent.futures as cf

from framework import db, images
from framework.client import AnynClient, strip_tags
from framework.tcmeta import tc


def shop(c, data, files=None):
    return c.post("shop.php", data, files=files, token_page="shop.php")


def msg(r):
    return strip_tags(r.text)


def inv(uid, key=None):
    sql, p = "SELECT * FROM user_inventory WHERE user_id=?", [uid]
    if key:
        sql, p = sql + " AND item_key=?", p + [key]
    return db.q(sql, p)


def frame(uid):
    return db.scalar("SELECT active_avatar_frame FROM users WHERE id=?", (uid,))


@tc("TC-GEM-01", "TS-09", "FR-09", "Nhiệm vụ hằng ngày: check-in 1 lần/ngày, nộp ý tưởng tối đa 3 lần/ngày, sang ngày mới được làm lại",
    "Tài khoản mới (0 gems)", ["Check-in 2 lần", "Nộp 4 ý tưởng", "Đổi log_date về hôm qua rồi check-in lại"],
    "daily_checkin (max 1, +5) | submit_idea (max 3, +10)",
    "Check-in lần 1: +5, lần 2: 'Daily limit reached' (+0); ý tưởng 1-3: +10 mỗi lần, ý tưởng thứ 4: +0; sang ngày mới check-in lại được (+5)",
    "Boundary Value Analysis (n = max, max+1) + State Transition", "Boundary", "High")
def test_gem_01(user, ev):
    r1 = shop(user, {"daily_checkin": "1"})
    g1 = db.gems(user.user_id)
    r2 = shop(user, {"daily_checkin": "1"})
    ev.note(f"check-in #1: gems={g1} '{msg(r1)[msg(r1).find('+5'):][:25]}'; #2: gems={db.gems(user.user_id)}, limit={'Daily limit reached' in r2.text}")
    assert g1 == 5 and db.gems(user.user_id) == 5 and "Daily limit reached" in r2.text
    for i in range(4):
        user.post("submit_idea.php", dict(title=f"cap{i}", appearance="a", context="b"))
    ev.note(f"sau 4 ý tưởng: gems={db.gems(user.user_id)} (mong đợi 5 + 3×10 = 35)")
    assert db.gems(user.user_id) == 35
    db.run("UPDATE gem_mission_log SET log_date=date('now','-1 day') WHERE user_id=?", (user.user_id,))
    shop(user, {"daily_checkin": "1"})
    assert db.gems(user.user_id) == 40


@tc("TC-GEM-02", "TS-09", "FR-09", "Mua khung avatar (25 gems): biên 24/25 gems, mua trùng, trang bị / gỡ khung",
    "Tài khoản mới", ["Có 24 gems → mua avt_gold", "Có 25 gems → mua avt_gold", "Mua lại avt_gold", "Gỡ khung (equip_key rỗng) rồi trang bị lại"],
    "gems = 24 | 25; item avt_gold (cost 25)",
    "24 gems: 'Not enough gems' (gems/inventory không đổi); 25 gems: mua được, gems = 0, khung tự được trang bị; mua lại: 'already own'; gỡ → NULL; trang bị lại thành công",
    "Boundary Value Analysis + State Transition", "Boundary", "High")
def test_gem_02(user, ev):
    db.set_gems(user.user_id, 24)
    r = shop(user, {"buy_item": "avt_gold"})
    ev.note(f"24 gems → {'Not enough gems' in r.text}, inventory={len(inv(user.user_id))}, gems={db.gems(user.user_id)}")
    assert "Not enough gems" in r.text and inv(user.user_id) == [] and db.gems(user.user_id) == 24
    db.set_gems(user.user_id, 25)
    r = shop(user, {"buy_item": "avt_gold"})
    ev.note(f"25 gems → gems={db.gems(user.user_id)}, inventory={len(inv(user.user_id))}, frame={frame(user.user_id)}")
    assert "Purchased: Gold Avatar Ring" in r.text and db.gems(user.user_id) == 0 and frame(user.user_id) == "avt_gold"
    db.set_gems(user.user_id, 100)
    r = shop(user, {"buy_item": "avt_gold"})
    assert "already own" in r.text and db.gems(user.user_id) == 100 and len(inv(user.user_id, "avt_gold")) == 1
    shop(user, {"equip_type": "avatar_frame", "equip_key": ""})
    assert frame(user.user_id) is None
    shop(user, {"equip_type": "avatar_frame", "equip_key": "avt_gold"})
    assert frame(user.user_id) == "avt_gold"


@tc("TC-GEM-03", "TS-09", "FR-09", "Thao tác mua/trang bị không hợp lệ: vật phẩm không tồn tại, khung chưa sở hữu, loại không hợp lệ",
    "Tài khoản có 500 gems, chưa sở hữu vật phẩm", ["buy_item='hack_item'", "equip avt_crystal khi chưa sở hữu", "equip_type='chat_frame'", "Gửi equip_type không kèm equip_key"],
    "hack_item | avt_crystal | chat_frame", "'Item not found' / 'You do not own this frame' / 'Invalid type'; gems & khung không đổi; trang không hiển thị PHP Warning/Notice",
    "Error Guessing + Equivalence Partitioning (invalid class)", "Invalid", "Medium", bug=["BUG-008"])
def test_gem_03(user, ev):
    db.set_gems(user.user_id, 500)
    assert "Item not found" in shop(user, {"buy_item": "hack_item"}).text
    assert "You do not own this frame" in shop(user, {"equip_type": "avatar_frame", "equip_key": "avt_crystal"}).text
    assert "Invalid type" in shop(user, {"equip_type": "chat_frame", "equip_key": "x"}).text
    r = shop(user, {"equip_type": "avatar_frame"})            # tampered form: equip_key missing
    warn = "Warning:" in r.text or "Notice:" in r.text or "Undefined" in r.text
    ev.note(f"gems={db.gems(user.user_id)}, khung={frame(user.user_id)}, PHP warning khi thiếu equip_key={warn}")
    assert db.gems(user.user_id) == 500 and frame(user.user_id) is None and inv(user.user_id) == []
    assert not warn, "trang phản hồi hiển thị PHP Warning (Undefined array key 'equip_key')"


@tc("TC-GEM-04", "TS-09", "FR-09", "Giới hạn voucher commission theo tháng: Publish 1 lần, Unlisted 3 lần (toàn shop)",
    "Bảng commission_monthly_limit trống; 5 tài khoản mới có 1000 gems", ["User A mua voucher Publish", "User B mua voucher Publish", "4 user mua voucher Unlisted"],
    "coupon_commission_publish (200 gems, max 1) | coupon_commission_unlisted (100 gems, max 3)",
    "Publish: người mua thứ 1 thành công (−200 gems), người thứ 2 bị 'Monthly limit reached'; Unlisted: 3 người đầu thành công, người thứ 4 bị từ chối và không bị trừ gems",
    "Boundary Value Analysis (limit, limit+1)", "Boundary", "High")
def test_gem_04(ev):
    db.run("DELETE FROM commission_monthly_limit")
    us = [AnynClient.new_user("qv", gems=1000) for _ in range(4)]
    r1 = shop(us[0], {"buy_item": "coupon_commission_publish"})
    r2 = shop(us[1], {"buy_item": "coupon_commission_publish"})
    ev.note(f"Publish: A='{'Purchased' in r1.text}', B='{'Monthly limit reached' in r2.text}', gems A={db.gems(us[0].user_id)}, gems B={db.gems(us[1].user_id)}")
    assert "Purchased" in r1.text and db.gems(us[0].user_id) == 800
    assert "Monthly limit reached" in r2.text and db.gems(us[1].user_id) == 1000
    res = [shop(u, {"buy_item": "coupon_commission_unlisted"}) for u in us]
    ok = ["Purchased" in r.text for r in res]
    ev.note(f"Unlisted: kết quả mua của 4 user = {ok}; gems user 4 = {db.gems(us[3].user_id)}")
    assert ok == [True, True, True, False] and db.gems(us[3].user_id) == 1000


@tc("TC-GEM-05", "TS-09", "FR-09", "Đổi gems lấy bộ ảnh nhân vật (image set): tải ảnh / liên kết, thiếu gems, dữ liệu sai",
    "Tài khoản có 100 gems", ["Gửi PNG + imageset_60", "Gửi lại khi còn 40 gems", "Gửi liên kết ftp://", "Dùng item avt_gold (không phải image_set)"],
    "imageset_60 (60 gems) | image_set_url=ftp://x", "Lần 1: gems 100→40, 1 yêu cầu 'pending' có ảnh trong /uploads/image_sets/; thiếu gems / URL sai / item sai: bị từ chối, không trừ gems, không tạo yêu cầu",
    "Equivalence Partitioning + Decision Table", "Valid", "High")
def test_gem_05(user, ev):
    db.set_gems(user.user_id, 100)
    r = shop(user, {"buy_image_set": "1", "image_set_item": "imageset_60"}, files={"image_set_file": ("ref.png", images.png(), "image/png")})
    reqs = db.q("SELECT * FROM image_set_requests WHERE user_id=?", (user.user_id,))
    ev.note(f"gems={db.gems(user.user_id)}, yêu cầu={[(q['item_key'], q['status'], q['image_url']) for q in reqs]}")
    assert "Image set request submitted" in r.text and db.gems(user.user_id) == 40
    assert len(reqs) == 1 and reqs[0]["status"] == "pending" and reqs[0]["image_url"].startswith("/anyn/uploads/image_sets/")
    r = shop(user, {"buy_image_set": "1", "image_set_item": "imageset_60", "image_set_url": "https://example.com/r.png"})
    assert "Not enough gems" in r.text and db.gems(user.user_id) == 40
    db.set_gems(user.user_id, 100)
    r = shop(user, {"buy_image_set": "1", "image_set_item": "imageset_60", "image_set_url": "ftp://example.com/r.png"})
    assert "valid http(s) URL" in r.text and db.gems(user.user_id) == 100
    r = shop(user, {"buy_image_set": "1", "image_set_item": "avt_gold", "image_set_url": "https://example.com/r.png"})
    assert "Invalid image set item" in r.text and db.gems(user.user_id) == 100
    assert db.scalar("SELECT COUNT(*) FROM image_set_requests WHERE user_id=?", (user.user_id,)) == 1


@tc("TC-GEM-06", "TS-09", "FR-09", "Liên kết ảnh dài (> 255 ký tự) không được làm mất gems khi yêu cầu image set thất bại",
    "Tài khoản có 100 gems", ["Gửi image_set_url = https://example.com/<300 ký tự>.png với imageset_60"],
    "URL dài 320 ký tự (hợp lệ theo safe_http_url, tối đa 500)", "Hoặc yêu cầu được tạo (gems −60) hoặc bị từ chối với thông báo và gems giữ nguyên 100; không được 'mất gems mà không có yêu cầu'",
    "Boundary Value Analysis (cột VARCHAR(255)) + Error Guessing", "Boundary", "High", bug=["BUG-009"])
def test_gem_06(user, ev):
    db.set_gems(user.user_id, 100)
    url = "https://example.com/" + "a" * 300 + ".png"
    r = shop(user, {"buy_image_set": "1", "image_set_item": "imageset_60", "image_set_url": url})
    n = db.scalar("SELECT COUNT(*) FROM image_set_requests WHERE user_id=?", (user.user_id,))
    g = db.gems(user.user_id)
    ev.note(f"URL {len(url)} ký tự → HTTP {r.status_code}, yêu cầu tạo={n}, gems={g}; trang: {strip_tags(r.text)[:120]!r}")
    assert (n == 1 and g == 40) or (n == 0 and g == 100), f"gems bị trừ ({100 - g}) nhưng không có yêu cầu nào (HTTP {r.status_code})"


@tc("TC-GEM-07", "TS-09", "FR-09", "Giao dịch đồng thời: cùng tài khoản đăng nhập trên nhiều thiết bị, số dư chỉ đủ 1 lần mua, không được làm gems âm",
    "Tài khoản có đúng 60 gems, đăng nhập sẵn trên 12 phiên (12 'thiết bị')", ["Mỗi lần thử: đặt gems=60 rồi gửi đồng thời 12 yêu cầu image set imageset_60 (60 gems) từ 12 phiên", "Lặp tối đa 100 lần, dừng khi phát hiện vượt số dư"],
    "gems = 60; 12 phiên song song; imageset_60", "Mỗi lần thử chỉ có 1 yêu cầu 'pending' được tạo và gems ≥ 0",
    "Experience-based (race condition / check-then-act)", "Invalid", "High", bug=["BUG-010"])
def test_gem_07(user, ev):
    # NOTE: requests of ONE php-session are serialised by PHP's session file lock, so the race needs several sessions
    # of the same account (= several devices/browsers), which is a realistic situation.
    sessions = []
    for _ in range(12):
        c = AnynClient()
        c.login(user.email, user.password)
        sessions.append((c, c.token("shop.php")))

    def go(p):
        c, tok = p
        return c.s.post(c.url("shop.php"), data={"csrf_token": tok, "buy_image_set": "1", "image_set_item": "imageset_60",
                                                 "image_set_url": "https://example.com/r.png"}, timeout=60).status_code

    n = g = 0
    for attempt in range(1, 101):
        db.set_gems(user.user_id, 60)
        db.run("DELETE FROM image_set_requests WHERE user_id=?", (user.user_id,))
        with cf.ThreadPoolExecutor(12) as ex:
            list(ex.map(go, sessions))
        n = db.scalar("SELECT COUNT(*) FROM image_set_requests WHERE user_id=?", (user.user_id,))
        g = db.gems(user.user_id)
        if n > 1 or g < 0:
            ev.note(f"VƯỢT SỐ DƯ ở lần thử {attempt}/100: {n} yêu cầu được tạo từ 60 gems, gems cuối = {g}")
            break
    else:
        ev.note("100 lần thử: không quan sát thấy vượt số dư")
    assert n <= 1 and g >= 0, f"mua đồng thời thành công {n} lần với số dư chỉ đủ 1 lần (gems cuối = {g})"
