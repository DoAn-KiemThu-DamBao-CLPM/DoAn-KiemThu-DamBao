"""TS-11 — Administration: access control, bot/theme management, moderation, commissions, statistics (FR-11)."""
import re

from framework import db, images
from framework.client import AnynClient, strip_tags, uniq
from framework.tcmeta import tc

MB5 = 5 * 1024 * 1024
ADMIN_PAGES = {            # page -> marker that only exists in the administrator's view
    "admin_bots.php": "save_bot",
    "admin_groups.php": "create_group",
    "admin_community.php": "moderate_id",
    "admin_stats.php": "Commission Status Breakdown",
    "admin_add_bot.php": "XÁC NHẬN THÊM BOT",
}


def png_file(name="b.png", pad_to=None):
    return {"bot_image_file": (name, images.png(pad_to=pad_to), "image/png")}


def save_bot(admin, files=None, **over):
    d = {"save_bot": "1", "name": uniq("QABot"), "description": "bot for QA"}
    d.update(over)
    return admin.post("admin_bots.php", d, files=files, token_page="admin_bots.php")


def new_post(uid, title, status="pending"):
    return db.run("INSERT INTO community_posts (user_id,title,image_url,rating,status) VALUES (?,?,?,?,?)",
                  (uid, title, "/anyn/uploads/avatars/avt_1.jpg", "sfw", status))


def new_commission(uid, title):
    return db.run("INSERT INTO commissions (user_id,title,appearance,context,image_url,amount_paid,is_private,status,admin_note) "
                  "VALUES (?,?,?,?,?,5,1,'Pending','')", (uid, title, "app", "ctx", ""))


@tc("TC-ADM-01", "TS-11", "FR-11", "Ma trận phân quyền: khách / người dùng / admin truy cập 5 trang quản trị",
    "3 vai trò: khách, user thường, admin", ["Mở lần lượt admin_bots, admin_groups, admin_community, admin_stats, admin_add_bot với từng vai trò", "User thường gửi POST moderate_id (duyệt bài) tới admin_community"],
    "5 trang × 3 vai trò", "Admin thấy đầy đủ giao diện quản trị; khách/user chỉ nhận thông báo từ chối hoặc chuyển hướng, KHÔNG thấy nội dung quản trị; POST của user thường không làm đổi dữ liệu",
    "Decision Table (role × page)", "Invalid", "High")
def test_adm_01(guest, user, admin, bob, ev):
    for page, marker in ADMIN_PAGES.items():
        ra, ru, rg = admin.get(page), user.get(page), guest.get(page)
        ev.note(f"{page}: admin={ra.status_code}, user={ru.status_code}{'→' + ru.headers['Location'] if 'Location' in ru.headers else ''}, "
                f"guest={rg.status_code}{'→' + rg.headers['Location'] if 'Location' in rg.headers else ''}")
        assert marker in ra.text, f"admin không thấy {page}"
        assert marker not in ru.text and marker not in rg.text, f"{page} lộ nội dung quản trị cho người không phải admin"
    pid = new_post(bob.user_id, uniq("pend"))
    r = user.post("admin_community.php", {"moderate_id": pid, "moderate_action": "approve"}, token_page="profile.php")
    ev.http("user thường POST duyệt bài", r)
    assert db.scalar("SELECT status FROM community_posts WHERE id=?", (pid,)) == "pending"


@tc("TC-ADM-02", "TS-11", "FR-11", "Thêm nhân vật (admin_bots): hợp lệ + chủ đề; thiếu tên/ảnh; tệp đội lốt ảnh; biên 5 MB",
    "Admin đã đăng nhập; chủ đề id 1, 2 tồn tại", ["Thêm bot với PNG hợp lệ + 2 chủ đề + ghim", "Thêm bot không tên", "Thêm bot không ảnh", "Tải file PHP đổi tên .png", "Tải PNG đúng 5 MB và 5 MB + 1"],
    "name | image | themes[]=1,2 | is_pinned", "Hợp lệ → bot mới có 2 chủ đề, is_pinned=1; thiếu tên/ảnh, file mã độc, 5MB+1 → bị từ chối (redirect kèm thông báo) và không tạo bot; đúng 5 MB được nhận",
    "Equivalence Partitioning + Boundary Value Analysis", "Boundary", "High")
def test_adm_02(admin, ev):
    created = []
    try:
        name = uniq("QABot")
        r = save_bot(admin, png_file(), name=name, **{"themes[]": ["1", "2"], "is_pinned": "on"})
        ev.http("thêm bot hợp lệ", r)
        bot = db.one("SELECT * FROM bots WHERE name=?", (name,))
        assert r.status_code == 302 and bot and bot["is_pinned"] == 1 and bot["image_url"].startswith("/anyn/uploads/")
        created.append(bot["id"])
        assert db.scalar("SELECT COUNT(*) FROM bot_themes WHERE bot_id=?", (bot["id"],)) == 2
        before = db.scalar("SELECT COUNT(*) FROM bots")
        bad = [("không tên", dict(name="   "), png_file()), ("không ảnh", {}, None),
               ("file PHP", {}, {"bot_image_file": ("x.png", images.PHP_SCRIPT, "image/png")}),
               ("5 MB + 1", {}, png_file(pad_to=MB5 + 1))]
        for label, over, files in bad:
            r = save_bot(admin, files, **over)
            ev.note(f"{label} → {r.status_code} {r.headers.get('Location', '')[:70]}")
            assert r.status_code == 302 and "msg=" in r.headers.get("Location", "")
        assert db.scalar("SELECT COUNT(*) FROM bots") == before
        name5 = uniq("QABot5")
        save_bot(admin, png_file(pad_to=MB5), name=name5)
        b5 = db.one("SELECT id FROM bots WHERE name=?", (name5,))
        ev.note(f"đúng 5 MB → {'được nhận' if b5 else 'bị từ chối'}")
        assert b5
        created.append(b5["id"])
    finally:
        for i in created:
            db.run("DELETE FROM bot_themes WHERE bot_id=?", (i,))
            db.run("DELETE FROM bots WHERE id=?", (i,))


@tc("TC-ADM-03", "TS-11", "FR-11", "Bộ lọc chủ đề cấm (NSFW/explicit): biến thể chữ hoa, dấu câu, khoảng trắng, full-width và ký tự giả dạng",
    "Admin đã đăng nhập", ["Thêm chủ đề: 'NSFW', 'n.s.f.w', 'Net-ori', ' R18 ', 'H E N T A I'", "Thêm chủ đề: 'ＮＳＦＷ' (full-width), 'nѕfw' (chữ Cyrillic ѕ)", "Thêm 'Cyberpunk' (hợp lệ) và 'Fantasy' (trùng)"],
    "danh sách biến thể ở bước 1–3", "Mọi biến thể của từ khoá cấm đều bị chặn 'This tag is not allowed'; 'Cyberpunk' được thêm; 'Fantasy' báo 'Theme already exists!'",
    "Equivalence Partitioning + Error Guessing (bypass)", "Invalid", "Medium", bug=["BUG-013"])
def test_adm_03(admin, ev):
    def add(n):
        return admin.post("admin_bots.php", {"add_theme": "1", "new_theme_name": n}, token_page="admin_bots.php")
    def blocked(r):
        return "not allowed" in r.text
    added = []
    try:
        ok_blocked = ["NSFW", "n.s.f.w", "Net-ori", " R18 ", "H E N T A I"]
        for n in ok_blocked:
            assert blocked(add(n)), f"'{n}' không bị chặn"
        r = add("Cyberpunk" + uniq("")[:4])
        assert r.status_code == 302
        added.append("Cyberpunk")
        assert "already exists" in add("Fantasy").text
        bypass = []
        for n in ["ＮＳＦＷ", "nѕfw", "ｈｅｎｔａｉ"]:
            rr = add(n)
            ok = blocked(rr)
            ev.note(f"{n!r} → {'bị chặn' if ok else 'ĐƯỢC THÊM (qua mặt bộ lọc)'}")
            if not ok:
                bypass.append(n)
        assert not bypass, f"biến thể sau qua mặt bộ lọc (normalizeThemeName chỉ giữ [a-z0-9]): {bypass}"
    finally:
        db.run("DELETE FROM themes WHERE name IN ('ＮＳＦＷ','nѕfw','ｈｅｎｔａｉ') OR name LIKE 'Cyberpunk%'")


@tc("TC-ADM-04", "TS-11", "FR-11", "Kiểm duyệt bài Community: duyệt / từ chối kèm lý do / hành động lạ",
    "3 bài ở trạng thái pending của bob; admin đã đăng nhập", ["Duyệt bài 1", "Từ chối bài 2 kèm lý do 'Too blurry'", "Gửi moderate_action='delete-all' cho bài 3"],
    "moderate_action = approve | reject | delete-all", "Bài 1: approved, admin_note NULL, hiện công khai; bài 2: rejected + lý do hiển thị cho bob, không hiện công khai; bài 3 giữ nguyên pending",
    "State Transition Testing", "Valid", "High")
def test_adm_04(admin, bob, guest, ev):
    t1, t2, t3 = uniq("ap"), uniq("rj"), uniq("xx")
    p1, p2, p3 = new_post(bob.user_id, t1), new_post(bob.user_id, t2), new_post(bob.user_id, t3)
    def mod(pid, act, note=""):
        return admin.post("admin_community.php", {"moderate_id": pid, "moderate_action": act, "admin_note": note}, token_page="admin_community.php")
    ev.http("approve", mod(p1, "approve"))
    mod(p2, "reject", "Too blurry")
    mod(p3, "delete-all")
    st = {i: db.one("SELECT status, admin_note, reviewed_at FROM community_posts WHERE id=?", (i,)) for i in (p1, p2, p3)}
    ev.note(f"trạng thái: {[(i, s['status'], s['admin_note']) for i, s in st.items()]}")
    assert st[p1]["status"] == "approved" and st[p1]["admin_note"] is None and st[p1]["reviewed_at"]
    assert st[p2]["status"] == "rejected" and st[p2]["admin_note"] == "Too blurry"
    assert st[p3]["status"] == "pending"
    pub = guest.get("community_gallery.php").text
    assert t1 in pub and t2 not in pub and t3 not in pub
    assert "Too blurry" in strip_tags(bob.get("community_gallery.php").text)


@tc("TC-ADM-05", "TS-11", "FR-11", "Quản lý đơn commission: đổi trạng thái + ghi chú, trạng thái lạ về Pending, chỉ chủ đơn thấy",
    "Đơn commission của user A; user B; user thường không phải admin", ["Admin đổi thành In Progress kèm ghi chú", "Admin đổi thành Completed", "Admin gửi status='Hacked'", "User thường gửi update_commission", "User B mở My Commissions"],
    "status = In Progress | Completed | Hacked", "Trạng thái và ghi chú cập nhật; 'Hacked' bị đưa về Pending; user thường không đổi được; A thấy ghi chú, B không thấy đơn của A",
    "State Transition Testing + Error Guessing", "Valid", "High")
def test_adm_05(admin, user, user2, ev):
    title = uniq("ComA")
    cid = new_commission(user.user_id, title)
    def upd(c, status, note, token_page="admin_bots.php"):
        return c.post("admin_bots.php", {"update_commission": "1", "com_id": cid, "status": status, "admin_note": note}, token_page=token_page)
    upd(admin, "In Progress", "Join Discord: https://discord.gg/qa-test")
    row = db.one("SELECT status, admin_note FROM commissions WHERE id=?", (cid,))
    ev.note(f"sau bước 1: {row}")
    assert row["status"] == "In Progress" and "discord.gg/qa-test" in row["admin_note"]
    page = user.get("my_commissions.php").text
    assert title in page and "discord.gg/qa-test" in page
    upd(admin, "Completed", "Done")
    assert db.scalar("SELECT status FROM commissions WHERE id=?", (cid,)) == "Completed"
    upd(admin, "Hacked", "x")
    assert db.scalar("SELECT status FROM commissions WHERE id=?", (cid,)) == "Pending"
    upd(user2, "Completed", "pwn", token_page="profile.php")
    assert db.scalar("SELECT status FROM commissions WHERE id=?", (cid,)) == "Pending"
    assert title not in user2.get("my_commissions.php").text


@tc("TC-ADM-06", "TS-11", "FR-11", "Bảng thống kê admin phản ánh đúng dữ liệu (Members, Characters, Ratings, Community Posts, Gem Transactions)",
    "Admin đã đăng nhập; DB đã có dữ liệu seed và giao dịch gems", ["Mở admin_stats.php", "So sánh từng ô thống kê với truy vấn trực tiếp DB"],
    "6 ô thống kê", "Mỗi ô bằng số liệu thực trong DB; ô 'Gem Transactions' phải > 0 khi đã có hoạt động nhận/tiêu gems",
    "Equivalence Partitioning (oracle: truy vấn DB)", "Valid", "Medium", bug=["BUG-014"])
def test_adm_06(admin, user, ev):
    user.post("shop.php", {"daily_checkin": "1"}, token_page="shop.php")      # make sure at least one gem event exists
    page = admin.get("admin_stats.php").text
    tiles = {m[1].strip(): int(m[0].replace(",", "")) for m in re.findall(r'<div class="val">([\d,]+)</div>\s*<div class="lbl">\s*([A-Za-z ]+?)\s*(?:<|\n)', page)}
    ev.note(f"ô thống kê đọc được: {tiles}")
    expect = {"Members": db.scalar("SELECT COUNT(*) FROM users"), "Characters": db.scalar("SELECT COUNT(*) FROM bots"),
              "Ratings": db.scalar("SELECT COUNT(*) FROM ratings"), "Community Posts": db.scalar("SELECT COUNT(*) FROM community_posts")}
    for k, v in expect.items():
        assert tiles.get(k) == v, f"ô '{k}' hiển thị {tiles.get(k)} nhưng DB có {v}"
    events = db.scalar("SELECT COALESCE(SUM(count),0) FROM gem_mission_log")
    ev.note(f"gem_mission_log có {events} sự kiện nhận gems; ô 'Gem Transactions' = {tiles.get('Gem Transactions')}")
    assert tiles.get("Gem Transactions", 0) > 0, "ô 'Gem Transactions' luôn bằng 0 (truy vấn bảng gem_transactions không tồn tại, lỗi bị nuốt bởi try/catch)"


@tc("TC-ADM-07", "TS-11", "FR-11", "Xoá nhân vật phải dọn dữ liệu liên quan (ratings, comments, chủ đề, nhóm)",
    "Bot test có 1 rating, 1 comment, 1 chủ đề, 1 thành viên nhóm", ["Admin gửi delete_id cho bot test", "Đếm bản ghi còn sót ở 4 bảng liên quan"],
    "delete_id = <bot test>", "Không còn bản ghi mồ côi ở ratings, comments, bot_themes, bot_group_members",
    "Error Guessing (data integrity)", "Valid", "Medium", bug=["BUG-015"])
def test_adm_07(admin, user, ev):
    bid = db.run("INSERT INTO bots (name,description,image_url,total_rating) VALUES (?,?,?,0)", (uniq("DelBot"), "d", "/anyn/uploads/avatars/avt_1.jpg"))
    db.run("INSERT INTO ratings (user_id,bot_id,score) VALUES (?,?,4)", (user.user_id, bid))
    db.run("INSERT INTO comments (user_id,bot_id,content) VALUES (?,?,'to be orphaned')", (user.user_id, bid))
    db.run("INSERT INTO bot_themes (bot_id,theme_id) VALUES (?,1)", (bid,))
    db.run("INSERT INTO bot_group_members (group_id,bot_id) VALUES (1,?)", (bid,))
    r = admin.post("admin_bots.php", {"delete_id": bid}, token_page="admin_bots.php")
    ev.http("xoá bot", r)
    assert db.scalar("SELECT COUNT(*) FROM bots WHERE id=?", (bid,)) == 0
    left = {t: db.scalar(f"SELECT COUNT(*) FROM {t} WHERE bot_id=?", (bid,)) for t in ("ratings", "comments", "bot_themes", "bot_group_members")}
    ev.note(f"bản ghi còn lại sau khi xoá bot #{bid}: {left}")
    db.run("DELETE FROM ratings WHERE bot_id=?", (bid,)); db.run("DELETE FROM comments WHERE bot_id=?", (bid,))
    db.run("DELETE FROM bot_group_members WHERE bot_id=?", (bid,))
    assert not any(left.values()), f"còn bản ghi mồ côi: { {k: v for k, v in left.items() if v} }"


@tc("TC-ADM-08", "TS-11", "FR-11", "Thêm nhân vật bằng trang admin_add_bot.php: gửi form đúng như trình duyệt (chỉ các trường có trong form)",
    "Admin đã đăng nhập", ["Mở admin_add_bot.php", "Điền tên, mô tả, chọn ảnh PNG", "Bấm nút 'XÁC NHẬN THÊM BOT' (form gửi đúng các trường có trong HTML)"],
    "name=QABot…; description; bot_image=PNG", "Form có csrf_token hợp lệ; bot được tạo (chuyển hướng/thông báo thành công); không bị 403 'Invalid or expired security token'",
    "Use-case testing + Error Guessing (rendered markup)", "Valid", "High", bug=["BUG-016"], auto="Script + Playwright (UI-07)")
def test_adm_08(admin, ev):
    name = uniq("UIBot")
    r, fields = admin.submit_form("admin_add_bot.php", "XÁC NHẬN THÊM BOT", overrides={"name": name, "description": "added through the page"},
                                  files={"bot_image": ("b.png", images.png(), "image/png")})
    html = admin.get("admin_add_bot.php").text
    broken = "<button <input" in html or bool(re.search(r"<button\s+<", html))
    ev.note(f"trường form gửi đi: {sorted(fields)}; markup nút bị hỏng: {broken}")
    ev.http("POST admin_add_bot (như trình duyệt)", r, strip_tags(r.text)[:80])
    bot = db.one("SELECT id FROM bots WHERE name=?", (name,))
    if bot:
        db.run("DELETE FROM bot_themes WHERE bot_id=?", (bot["id"],))
        db.run("DELETE FROM bots WHERE id=?", (bot["id"],))
    assert r.status_code != 403 and bot, f"HTTP {r.status_code}: form không chứa csrf_token nên mọi lần gửi đều bị chặn ('Security Error')"
