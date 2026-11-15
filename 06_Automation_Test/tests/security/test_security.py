"""Non-functional: security tests (OWASP-oriented, black-box).  Results -> results/<cycle>/nonfunctional_results.json"""
import hashlib
import os
import re

import requests

from framework import db, images
from framework.client import AnynClient, strip_tags, uniq
from framework.config import ADMIN, APP, BASE_URL, PAGES, UPLOAD_DIR
from framework.tcmeta import nf_case

XSS = '"><img src=x onerror=alert(1)><script>alert(1)</script>'
RAW = ("<script>alert(1)</script>", "<img src=x onerror=alert(1)>")


def raw_xss(html):
    return [r for r in RAW if r in html]


# ------------------------------------------------------------------------------------------------------------------
@nf_case("NF-SEC-01", "Security / CSRF", "Bảo vệ CSRF trên các thao tác thay đổi dữ liệu",
         "Mọi POST thay đổi trạng thái phải bị từ chối khi thiếu token hoặc dùng token của phiên khác (OWASP A01/CSRF)",
         ["Với 10 endpoint POST: gửi không có csrf_token", "Gửi token lấy từ phiên của người khác", "Gửi token đúng (đối chứng)"],
         "Thiếu token / token phiên khác → HTTP 403 và không đổi dữ liệu; token đúng → không bị 403")
def test_nf_sec_01(ev):
    victim = AnynClient.new_user("csrf")
    other = AnynClient.new_user("csrfx")
    admin = AnynClient.as_(ADMIN)
    cases = [  # (client, path, data, token_page)
        (victim, "profile.php", {"change_password": "1", "current_password": victim.password, "new_password": "Hacked123x", "new_password_confirm": "Hacked123x"}, "profile.php"),
        (victim, "shop.php", {"daily_checkin": "1"}, "shop.php"),
        (victim, "ideas.php", {"upvote_id": "1"}, "ideas.php"),
        (victim, "submit_idea.php", {"title": "t", "appearance": "a", "context": "c"}, "submit_idea.php"),
        (victim, "bot_detail.php?id=1", {"submit_comment": "1", "content": "csrf"}, "bot_detail.php?id=1"),
        (victim, "user.php?id=3", {"follow_action": "follow"}, "user.php?id=3"),
        (victim, "gallery.php", {"react": "1", "gallery_id": "1", "reaction_type": "like"}, "gallery.php"),
        (victim, "community_gallery.php", {"react": "1", "post_id": "1", "reaction_type": "like"}, "community_gallery.php"),
        (victim, "commission.php", {"submit_commission": "1", "title": "t", "appearance": "a", "context": "c", "amount": "5"}, "commission.php"),
        (admin, "admin_bots.php", {"delete_id": "999999"}, "admin_bots.php"),
    ]
    bad = []
    snapshot = {t: db.scalar(f"SELECT COUNT(*) FROM {t}") for t in ("ideas", "comments", "commissions", "user_follows", "gallery_reactions", "community_reactions", "idea_upvotes")}
    foreign = other.token("profile.php")
    for c, path, data, tp in cases:                       # 1) blocked attempts: no token / token of another session
        r1 = c.post(path, data, csrf=False)
        r2 = c.post(path, dict(data, csrf_token=foreign), csrf=False)
        ev.note(f"{path:26s} không token={r1.status_code} | token phiên khác={r2.status_code}")
        if r1.status_code != 403 or r2.status_code != 403:
            bad.append(path)
    r = AnynClient().post("login.php", {"email": "alice@anyn.test", "password": "x"}, csrf=False)
    ev.note(f"login.php không token = {r.status_code} (login CSRF)")
    after = {t: db.scalar(f"SELECT COUNT(*) FROM {t}") for t in snapshot}
    ev.note(f"dữ liệu sau các yêu cầu bị chặn: gems={db.gems(victim.user_id)}, bảng thay đổi={ {t: (snapshot[t], after[t]) for t in snapshot if snapshot[t] != after[t]} }")
    assert r.status_code == 403
    assert db.gems(victim.user_id) == 0 and after == snapshot, "yêu cầu bị chặn vẫn làm thay đổi dữ liệu"
    assert AnynClient().login(victim.email, victim.password).status_code == 302, "mật khẩu bị đổi bằng yêu cầu thiếu token"
    for c, path, data, tp in cases[1:9]:                  # 2) control: valid token must NOT be rejected
        r3 = c.post(path, data, token_page=tp)
        ev.note(f"[đối chứng] {path:26s} token đúng={r3.status_code}")
        if r3.status_code == 403:
            bad.append(path + " (token đúng bị chặn)")
    assert not bad, f"endpoint không được bảo vệ đúng: {bad}"


# ------------------------------------------------------------------------------------------------------------------
@nf_case("NF-SEC-02", "Security / Session", "Quản lý phiên: cờ cookie, chống session fixation, strict mode, huỷ phiên khi đăng xuất",
         "Cookie phiên có HttpOnly + SameSite; ID phiên đổi sau đăng nhập; ID do kẻ tấn công đặt không được chấp nhận; cookie cũ vô hiệu sau logout",
         ["Đọc Set-Cookie", "So sánh PHPSESSID trước/sau đăng nhập", "Gửi PHPSESSID tự đặt", "Dùng lại cookie cũ sau logout"],
         "Đạt cả 4 điểm; 'Secure' chỉ bắt buộc khi chạy HTTPS (ghi nhận là khuyến nghị)")
def test_nf_sec_02(ev):
    c = AnynClient()
    r0 = c.get("login.php")
    sid_before = c.s.cookies.get("PHPSESSID")
    sc = r0.headers.get("Set-Cookie", "")
    ev.note("Set-Cookie: " + re.sub(r"PHPSESSID=\w+", "PHPSESSID=…", sc))
    assert "httponly" in sc.lower() and "samesite=lax" in sc.lower()
    ev.note(f"cờ Secure: {'có' if 'secure' in sc.lower() else 'KHÔNG (chỉ chấp nhận được trên HTTP/XAMPP; bật khi triển khai HTTPS)'}")
    u = AnynClient.new_user("sess")
    c2 = AnynClient()
    c2.get("login.php")
    before = c2.s.cookies.get("PHPSESSID")
    c2.login(u.email, u.password)
    after = c2.s.cookies.get("PHPSESSID")
    ev.note(f"PHPSESSID trước/sau đăng nhập: {before[:6]}… → {after[:6]}…")
    assert before != after, "session fixation: ID phiên không đổi sau đăng nhập"
    fake = requests.Session()
    fake.cookies.set("PHPSESSID", "attackerchosensessionid0123456789", domain="127.0.0.1")
    rr = fake.get(PAGES + "/login.php")
    new_sid = fake.cookies.get("PHPSESSID")
    ev.note(f"gửi PHPSESSID tự đặt → máy chủ cấp ID: {new_sid[:6]}…")
    assert "attackerchosensessionid0123456789" not in rr.headers.get("Set-Cookie", "") or new_sid != "attackerchosensessionid0123456789"
    old_cookie = c2.s.cookies.get("PHPSESSID")
    c2.logout()
    replay = requests.Session()
    replay.cookies.set("PHPSESSID", old_cookie, domain="127.0.0.1")
    r = replay.get(PAGES + "/profile.php", allow_redirects=False)
    ev.note(f"dùng lại cookie cũ sau logout → HTTP {r.status_code} {r.headers.get('Location', '')}")
    assert r.status_code == 302 and "login" in r.headers.get("Location", "")


# ------------------------------------------------------------------------------------------------------------------
@nf_case("NF-SEC-03", "Security / Headers", "HTTP security headers và rò rỉ thông tin phiên bản",
         "Có các header phòng thủ cơ bản; ghi nhận các khuyến nghị còn thiếu",
         ["GET trang chủ, login, profile, 404", "Kiểm tra header"],
         "Bắt buộc: X-Content-Type-Options=nosniff, X-Frame-Options, Referrer-Policy, CSP có frame-ancestors. Khuyến nghị (ghi nhận, không tính lỗi): script-src trong CSP, ẩn X-Powered-By, Cache-Control cho trang đã đăng nhập")
def test_nf_sec_03(ev):
    c = AnynClient.as_(ADMIN)
    for path in ("index.php", "login.php", "profile.php", "bot_detail.php?id=1", "gallery.php"):
        r = c.get(path, allow_redirects=True)
        h = r.headers
        assert h.get("X-Content-Type-Options", "").lower() == "nosniff", path
        assert h.get("X-Frame-Options", "").upper() in ("SAMEORIGIN", "DENY"), path
        assert "strict-origin" in h.get("Referrer-Policy", "") or "no-referrer" in h.get("Referrer-Policy", ""), path
        assert "frame-ancestors" in h.get("Content-Security-Policy", ""), path
    h = c.get("index.php", allow_redirects=True).headers
    csp = h.get("Content-Security-Policy", "")
    ev.note(f"CSP = {csp}")
    ev.note(f"[khuyến nghị] CSP có script-src/default-src: {'script-src' in csp or 'default-src' in csp} → {'đạt' if ('script-src' in csp or 'default-src' in csp) else 'CSP hiện không giảm thiểu được XSS'}")
    ev.note(f"[khuyến nghị] X-Powered-By: {h.get('X-Powered-By', '(không có)')}")
    ev.note(f"[khuyến nghị] Strict-Transport-Security: {h.get('Strict-Transport-Security', '(không có — chấp nhận được trên HTTP)')}")
    ev.note(f"Cache-Control (đã đăng nhập): {h.get('Cache-Control')}")


# ------------------------------------------------------------------------------------------------------------------
@nf_case("NF-SEC-04", "Security / XSS", "Quét XSS (lưu trữ và phản xạ) trên mọi điểm nhập liệu hiển thị lại",
         "Dữ liệu người dùng phải được escape khi xuất ra HTML (OWASP A03)",
         ["Nhập payload XSS vào bio, bình luận, ý tưởng, commission, tiêu đề community, tên/mô tả bot, tham số tìm kiếm/msg",
          "Tải các trang hiển thị rồi tìm thẻ <script>/<img onerror> nguyên bản"],
         "Không trang nào chứa payload ở dạng thô (phải là &lt;script&gt;…)")
def test_nf_sec_04(ev):
    u = AnynClient.new_user("xss")
    admin = AnynClient.as_(ADMIN)
    hits = {}
    u.post("profile.php", {"username": u.username, "bio": XSS, "avatar_choice": "avt_1.jpg"})
    u.post("bot_detail.php?id=40", {"submit_comment": "1", "content": XSS})
    u.post("submit_idea.php", {"title": XSS, "appearance": XSS, "context": XSS})
    u.post("commission.php", {"submit_commission": "1", "title": XSS, "appearance": XSS, "context": XSS, "amount": "5"})
    u.post("community_upload.php", {"submit_community": "1", "title": XSS, "agree_guidelines": "1"}, files={"image_file": ("a.png", images.png(), "image/png")},
           token_page="community_upload.php")
    pid = db.scalar("SELECT id FROM community_posts WHERE user_id=? ORDER BY id DESC", (u.user_id,))
    bot_name = "XSSBot" + uniq("")
    admin.post("admin_bots.php", {"save_bot": "1", "name": bot_name + XSS[:40], "description": XSS}, files={"bot_image_file": ("a.png", images.png(), "image/png")}, token_page="admin_bots.php")
    # the moderation queue only lists PENDING posts: read it BEFORE approving, otherwise the sink would be empty (vacuous check)
    pending_html = admin.get("admin_community.php", allow_redirects=True).text
    sinks = {
        "user.php (bio)": (u, f"user.php?id={u.user_id}"), "bot_detail.php (comment)": (u, "bot_detail.php?id=40"),
        "ideas.php (idea fields)": (u, "ideas.php"), "my_commissions.php": (u, "my_commissions.php"),
        "admin_bots.php (commission + bot)": (admin, "admin_bots.php"), "admin_community.php (title)": (admin, "admin_community.php"),
        "index.php (bot name)": (u, "index.php?search=" + bot_name),
        "reflect: index.php?search": (u, "index.php?search=" + requests.utils.quote(XSS) + "&theme=" + requests.utils.quote(XSS)),
        "reflect: admin_bots.php?msg": (admin, "admin_bots.php?msg=" + requests.utils.quote(XSS)),
        "reflect: admin_groups.php?msg": (admin, "admin_groups.php?msg=" + requests.utils.quote(XSS)),
        "reflect: ideas.php?msg": (u, "ideas.php?msg=" + requests.utils.quote(XSS) + "&error=" + requests.utils.quote(XSS)),
        "reflect: community_gallery.php?msg": (u, "community_gallery.php?msg=" + requests.utils.quote(XSS)),
    }
    admin.post("admin_community.php", {"moderate_id": pid, "moderate_action": "approve"}, token_page="admin_community.php")
    sinks["community_gallery.php (approved title)"] = (u, "community_gallery.php")
    new_bot = db.scalar("SELECT id FROM bots WHERE name LIKE ? ORDER BY id DESC", (bot_name + "%",))
    sinks["bot_detail.php (bot name + description)"] = (u, f"bot_detail.php?id={new_bot}")
    not_shown = []
    for label, (c, path) in sinks.items():
        html = pending_html if label == "admin_community.php (title)" else c.get(path, allow_redirects=True).text
        found = raw_xss(html)
        escaped = "&lt;script&gt;" in html or "&lt;img" in html
        ev.note(f"{label:42s} thô={bool(found)} | đã escape={escaped}")
        if found:
            hits[label] = found
        elif not escaped:
            not_shown.append(label)        # payload not rendered at all on this page -> no conclusion for this sink
    ev.note(f"{len(sinks) - len(not_shown)}/{len(sinks)} điểm hiển thị payload (đã escape); không hiển thị (không kết luận): {not_shown or 'không có'}")
    assert not hits, f"XSS: payload thô xuất hiện tại {list(hits)}"


# ------------------------------------------------------------------------------------------------------------------
@nf_case("NF-SEC-05", "Security / Injection", "Quét SQL injection trên tham số GET/POST",
         "Các tham số không được làm thay đổi câu truy vấn (OWASP A03); ứng dụng dùng prepared statements",
         ["Gửi 5 payload SQLi vào các tham số id/page/search/sort/theme/q/token/msg của 12 trang", "Kiểm tra mã trạng thái, thông báo lỗi SQL và số bản ghi users"],
         "Không HTTP 5xx, không thông báo SQLSTATE/syntax, không lộ hash mật khẩu, bảng users không đổi")
def test_nf_sec_05(ev):
    payloads = ["1' OR '1'='1", "1 OR 1=1", "1; DROP TABLE users--", "' UNION SELECT username,password_hash,3,4,5 FROM users--", "%' AND 1=2 UNION SELECT 1--"]
    admin = AnynClient.as_(ADMIN)
    guest = AnynClient()
    targets = [("bot_detail.php?id={}", guest), ("user.php?id={}", guest), ("edit_idea.php?id={}", admin), ("index.php?page={}", guest),
               ("index.php?search={}", guest), ("index.php?sort={}", guest), ("index.php?theme={}", guest),
               ("search_suggestions.php?q={}", guest), ("reset_password.php?token={}", guest), ("gallery.php?group={}", guest),
               ("community_gallery.php?page={}", guest), ("admin_groups.php?edit={}", admin)]
    users_before = db.scalar("SELECT COUNT(*) FROM users")
    problems = []
    total = 0
    for tpl, c in targets:
        for p in payloads:
            r = c.get(tpl.format(requests.utils.quote(p, safe="")), allow_redirects=True)
            total += 1
            body = r.text
            if r.status_code >= 500 or "SQLSTATE" in body or "syntax error" in body.lower() or "$2y$" in body or "Fatal error" in body:
                problems.append((tpl, p, r.status_code))
    ev.note(f"{total} yêu cầu gửi đi; vấn đề phát hiện: {problems}")
    assert db.scalar("SELECT COUNT(*) FROM users") == users_before, "bảng users bị thay đổi"
    assert not problems, f"nghi ngờ SQLi/lỗi: {problems[:5]}"


# ------------------------------------------------------------------------------------------------------------------
@nf_case("NF-SEC-06", "Security / Upload", "An toàn khi tải tệp: đuôi kép, đội lốt ảnh, polyglot, SVG, path traversal",
         "Tệp tải lên không bao giờ được lưu với đuôi thực thi và không được thực thi (OWASP A04/A08)",
         ["Tải 7 loại tệp độc hại/biến thể lên submit_idea.php", "Kiểm tra phản hồi, tên tệp lưu, thư mục uploads"],
         "Tệp PHP/SVG/đuôi kép bị từ chối; ảnh thật tên .php được lưu với đuôi theo MIME (.png); polyglot GIF chỉ lưu .gif và được phục vụ như ảnh; không tệp nào ghi ra ngoài thư mục uploads")
def test_nf_sec_06(ev):
    u = AnynClient.new_user("up")
    gif_poly = b"GIF89a" + b"<?php echo 'PWNED'; ?>" + b"\x00" * 64
    svg = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
    cases = [("evil.php", images.PHP_SCRIPT, False), ("evil.php.png", images.PHP_SCRIPT, False), ("x.svg", svg, False),
             ("doc.html", images.HTML_SCRIPT, False), ("real.php", images.png(), True), ("../../../../tmp/traversal.png", images.png(), True),
             ("poly.gif", gif_poly, True)]
    stored = []
    before = {os.path.join(d, f) for d, _, fs in os.walk(UPLOAD_DIR) for f in fs}
    for name, body, should_pass in cases:
        n0 = db.scalar("SELECT COUNT(*) FROM ideas WHERE user_id=?", (u.user_id,))
        r = u.post("submit_idea.php", {"title": "up", "appearance": "a", "context": "c"}, files={"idea_image_file": (name, body, "image/png")}, token_page="submit_idea.php")
        n1 = db.scalar("SELECT COUNT(*) FROM ideas WHERE user_id=?", (u.user_id,))
        ok = n1 == n0 + 1 and "Idea submitted" in r.text
        url = db.scalar("SELECT image_url FROM ideas WHERE user_id=? ORDER BY id DESC", (u.user_id,)) if ok else None
        ev.note(f"{name!r:34s} → {'ĐƯỢC NHẬN, lưu: ' + str(url) if ok else 'bị từ chối'} (kỳ vọng {'nhận' if should_pass else 'từ chối'})")
        assert ok == should_pass, f"{name}: kết quả không như kỳ vọng"
        if ok:
            assert not re.search(r"\.(php\d?|phtml|phar|html?|svg)$", url, re.I), f"lưu với đuôi nguy hiểm: {url}"
            stored.append(url)
    after = {os.path.join(d, f) for d, _, fs in os.walk(UPLOAD_DIR) for f in fs}
    assert all(f.startswith(UPLOAD_DIR) for f in after) and not os.path.exists("/tmp/traversal.png")
    gif_url = [s for s in stored if s.endswith(".gif")][0]
    rr = requests.get(BASE_URL + gif_url)
    ev.note(f"polyglot GIF phục vụ với Content-Type={rr.headers.get('Content-Type')}, chứa chuỗi PHP thô={b'<?php' in rr.content}, PHP thực thi={b'PWNED' in rr.content and b'<?php' not in rr.content}")
    assert rr.headers.get("Content-Type", "").startswith("image/") and not (b"PWNED" in rr.content and b"<?php" not in rr.content)


# ------------------------------------------------------------------------------------------------------------------
@nf_case("NF-SEC-07", "Security / Credentials", "Lưu trữ mật khẩu và token đặt lại",
         "Mật khẩu phải được băm bằng thuật toán mạnh có salt; token đặt lại không lưu dạng rõ (OWASP A02)",
         ["Đọc users.password_hash của tài khoản mới", "Yêu cầu đặt lại mật khẩu và so token trong liên kết với giá trị trong DB"],
         "Hash dạng bcrypt ($2y$, 60 ký tự), hai tài khoản cùng mật khẩu có hash khác nhau, không có mật khẩu rõ trong DB; token trong DB = SHA-256 của token gửi cho người dùng")
def test_nf_sec_07(ev):
    a = AnynClient.new_user("pw")
    b = AnynClient()
    b.register(uniq("pw"), f"{uniq('pw')}@qa.test", a.password)
    h1 = db.scalar("SELECT password_hash FROM users WHERE id=?", (a.user_id,))
    h2 = db.scalar("SELECT password_hash FROM users WHERE email LIKE 'pw%@qa.test' AND id<>? ORDER BY id DESC", (a.user_id,))
    ev.note(f"hash: {h1[:7]}… (len {len(h1)}); hai hash cùng mật khẩu khác nhau: {h1 != h2}")
    assert h1.startswith("$2y$") and len(h1) == 60 and h1 != h2
    assert db.scalar("SELECT COUNT(*) FROM users WHERE password_hash=? OR email=? OR bio=?", (a.password, a.password, a.password)) == 0
    r = AnynClient().post("forgot_password.php", {"email": a.email})
    m = re.search(r"reset_password\.php\?token=([a-f0-9]{64})", r.text)
    if not m:
        ev.note("môi trường production: không hiển thị liên kết → không đối chiếu được token (xem BUG-001)")
        return
    tok = m.group(1)
    cols = [c["name"] for c in db.q("PRAGMA table_info(password_resets)")]
    stored = db.scalar(f"SELECT {'token_hash' if 'token_hash' in cols else cols[2]} FROM password_resets WHERE user_id=? ORDER BY id DESC", (a.user_id,))
    ev.note(f"cột password_resets: {cols}; DB lưu {stored[:10]}… ; sha256(token)={hashlib.sha256(tok.encode()).hexdigest()[:10]}…")
    assert stored != tok and stored == hashlib.sha256(tok.encode()).hexdigest()


# ------------------------------------------------------------------------------------------------------------------
@nf_case("NF-SEC-08", "Security / Authorization", "Chống leo thang đặc quyền và mass-assignment",
         "Người dùng không thể tự gán role/gems/total_spent hay truy cập chức năng admin bằng tham số thừa (OWASP A01/A04)",
         ["Đăng ký và lưu profile kèm role=admin, gems=999, total_spent=999, id=1", "Gửi hành động admin bằng phiên user thường"],
         "role='user', gems=0, total_spent=0; không hành động admin nào có hiệu lực")
def test_nf_sec_08(ev):
    name = uniq("ma")
    c = AnynClient()
    c.post("register.php", {"username": name, "email": f"{name}@qa.test", "password": "Passw0rd!x", "password_confirm": "Passw0rd!x",
                            "role": "admin", "gems": "999", "total_spent": "999", "id": "1", "is_admin": "1"})
    c.login(f"{name}@qa.test", "Passw0rd!x")
    c.post("profile.php", {"username": name, "bio": "x", "avatar_choice": "avt_1.jpg", "role": "admin", "gems": "999", "total_spent": "999"})
    row = db.one("SELECT id, role, gems, total_spent FROM users WHERE username=?", (name,))
    ev.note(f"sau mass-assignment: {row}")
    assert row["id"] != 1 and row["role"] == "user" and (row["gems"] or 0) == 0 and float(row["total_spent"] or 0) == 0
    acts = [("admin_bots.php", {"delete_id": "1"}), ("admin_bots.php", {"add_theme": "1", "new_theme_name": "Pwn" + name}),
            ("admin_community.php", {"moderate_id": "1", "moderate_action": "reject"}), ("ideas.php", {"idea_complete": "1", "idea_id": "1", "bot_id": "1", "bot_visibility": "published"})]
    for path, data in acts:
        c.post(path, data, token_page="profile.php")
    assert db.scalar("SELECT COUNT(*) FROM bots WHERE id=1") == 1
    assert db.scalar("SELECT COUNT(*) FROM themes WHERE name=?", ("Pwn" + name,)) == 0
    assert db.scalar("SELECT status FROM community_posts WHERE id=1") == "approved"
    assert db.scalar("SELECT work_status FROM ideas WHERE id=1") == "open"


# ------------------------------------------------------------------------------------------------------------------
@nf_case("NF-SEC-09", "Security / Authorization", "Ngữ nghĩa phản hồi khi bị từ chối quyền (HTTP 403 hoặc chuyển hướng)",
         "Truy cập trái phép trang quản trị phải trả 401/403 hoặc 302 — không trả 200 'OK' kèm thông báo (OWASP A01 / ASVS 4.1)",
         ["Khách và user thường mở 5 trang quản trị", "Ghi lại mã trạng thái"],
         "Mọi phản hồi từ chối có mã 302/401/403", bug=["BUG-017"])
def test_nf_sec_09(ev):
    guest, user = AnynClient(), AnynClient.new_user("den")
    bad = []
    for page in ("admin_bots.php", "admin_groups.php", "admin_community.php", "admin_stats.php", "admin_add_bot.php"):
        for who, c in (("guest", guest), ("user", user)):
            r = c.get(page)
            ev.note(f"{page:22s} {who:5s} → HTTP {r.status_code}")
            if r.status_code not in (302, 401, 403):
                bad.append(f"{page}/{who}={r.status_code}")
    assert not bad, f"trang quản trị trả 200 cho người không có quyền (auth.php đã có requireAdmin() trả 403 nhưng không được dùng): {bad}"


# ------------------------------------------------------------------------------------------------------------------
@nf_case("NF-SEC-10", "Security / Exposure", "Tệp nội bộ không được truy cập được qua web",
         "Mã nguồn SQL, tệp workspace, include/config không nên tải được từ web root (OWASP A05)",
         ["GET /anyn/sql/*.sql, /anyn/*.code-workspace, /anyn/includes/header.php, /anyn/config/database.php"],
         "Mọi đường dẫn trả 403/404 (hoặc nội dung rỗng với tệp .php cấu hình)", bug=["BUG-018"])
def test_nf_sec_10(ev):
    files = ["sql/gems_shop.sql", "sql/accounts_security.sql", "sql/ideas_workflow.sql", "gygyu.code-workspace", "includes/header.php"]
    leaked = []
    for f in files:
        r = requests.get(f"{APP}/{f}")
        ev.note(f"/anyn/{f:30s} → HTTP {r.status_code}, {len(r.content)} byte")
        if r.status_code == 200 and len(r.content) > 0:
            leaked.append(f)
    root_ht = os.path.join(os.environ.get("ANYN_WORK", ""), "sut", "anyn", ".htaccess")
    if leaked and os.path.isfile(root_ht) and "Require all denied" in open(root_ht, encoding="utf-8").read():
        # The fix is an Apache rule (.htaccess).  PHP's built-in server used by this test bench ignores .htaccess, so the
        # fix can only be inspected statically here; it must be re-tested on the real Apache/XAMPP (see Test Plan, threats).
        ev.note(".htaccess có quy tắc 'Require all denied' (kiểm tra tĩnh OK) nhưng máy chủ PHP built-in bỏ qua .htaccess")
        import pytest
        pytest.skip("BLOCKED: bản vá là quy tắc Apache (.htaccess) — máy chủ thử nghiệm PHP built-in không thi hành; cần chạy lại trên XAMPP/Apache")
    ev.note("Lưu ý: thư mục uploads/* có .htaccess chặn thực thi; thư mục gốc, sql/, includes/, config/ KHÔNG có .htaccess/index chặn truy cập (đúng cả trên Apache)")
    assert not leaked, f"tải được từ web: {leaked}"


# ------------------------------------------------------------------------------------------------------------------
@nf_case("NF-SEC-11", "Security / Brute force", "Giới hạn đăng nhập không bị vượt bằng header X-Forwarded-For",
         "Bộ đếm khoá đăng nhập dựa trên REMOTE_ADDR, không tin header do client gửi",
         ["Gửi 5 lần đăng nhập sai với 5 giá trị X-Forwarded-For khác nhau", "Gửi lần thứ 6 với mật khẩu đúng"],
         "Lần 6 vẫn bị khoá ('Too many failed attempts')")
def test_nf_sec_11(ev):
    c = AnynClient()
    for i in range(5):
        c.s.headers["X-Forwarded-For"] = f"10.9.8.{i}"
        c.login("alice@anyn.test", f"bad{i}Pass!")
    c.s.headers["X-Forwarded-For"] = "10.9.8.99"
    r = c.login("alice@anyn.test", "User@12345")
    ev.note(f"lần 6 với XFF mới: HTTP {r.status_code}; {'bị khoá' if 'Too many' in r.text else 'ĐĂNG NHẬP ĐƯỢC (bị vượt qua)'}")
    assert "Too many" in r.text and r.status_code == 200
