"""TS-04 — Profile, avatar, public member page, follow (FR-04)."""
import os

from framework import db
from framework.client import AnynClient, strip_tags, uniq
from framework.config import UPLOAD_DIR
from framework.images import GIF_POLYGLOT, PHP_SCRIPT, png
from framework.tcmeta import tc


def _save(c, **kw):
    d = {"username": c.username, "bio": "", "avatar_choice": ""}
    d.update(kw)
    files = d.pop("_files", None)
    return c.post("profile.php", d, files=files)


@tc("TC-PRF-01", "TS-04", "FR-04", "Truy cập trang hồ sơ: khách vào Profile bị chuyển tới đăng nhập; trang member công khai với id hợp lệ / không tồn tại / không phải số", "Chưa đăng nhập",
    ["Mở /pages/profile.php", "Mở user.php?id=2", "Mở user.php?id=99999, abc, 0, -1"], "2 | 99999 | abc | 0 | -1",
    "Profile → 302 về login; id=2 hiển thị alice_qa (200); id không tồn tại hoặc không phải số → HTTP 404 'Member not found'",
    "Decision Table (role × page) + Equivalence Partitioning", "Invalid", "High")
def test_prf_01(guest, ev):
    r = guest.get("profile.php")
    ev.http("GET profile (guest)", r)
    assert r.status_code == 302 and "login" in r.headers.get("Location", "")
    r = guest.get("user.php?id=2")
    assert r.status_code == 200 and "alice_qa" in r.text
    for bad in ("99999", "abc", "0", "-1"):
        r = guest.get("user.php?id=" + bad)
        ev.note(f"id={bad}: HTTP {r.status_code}")
        assert r.status_code == 404 and "Member not found" in r.text, f"id={bad} → {r.status_code}"


@tc("TC-PRF-02", "TS-04", "FR-04", "Cập nhật username và bio hợp lệ", "Đã đăng nhập",
    ["Mở Profile", "Đổi username, nhập bio", "Bấm Save"], "username=<mới>; bio='Xin chào, mình thích fantasy'",
    "Thông báo 'Profile updated successfully!'; DB cập nhật; navbar hiển thị tên mới", "Equivalence Partitioning (valid class)", "Valid", "High")
def test_prf_02(user, ev):
    new = uniq("nm")
    r = _save(user, username=new, bio="Xin chào, mình thích fantasy")
    assert "Profile updated successfully" in strip_tags(r.text), strip_tags(r.text)[:200]
    row = db.one("SELECT username, bio FROM users WHERE id=?", (user.user_id,))
    assert row["username"] == new and row["bio"] == "Xin chào, mình thích fantasy"
    ev.note(f"DB: {row}")


@tc("TC-PRF-03", "TS-04", "FR-04", "Đổi sang username đã tồn tại (khác hoa/thường) bị từ chối", "Có user alice_qa",
    ["Đổi username thành ALICE_QA"], "ALICE_QA", "Lỗi 'already taken'; DB không đổi", "Equivalence Partitioning (invalid class)", "Invalid", "High")
def test_prf_03(user, ev):
    old = user.username
    r = _save(user, username="ALICE_QA")
    assert "already taken" in strip_tags(r.text), strip_tags(r.text)[:200]
    assert db.scalar("SELECT username FROM users WHERE id=?", (user.user_id,)) == old


@tc("TC-PRF-04", "TS-04", "FR-04", "Giá trị biên khi sửa profile: username 2 / 3 / 30 / 31 ký tự và Bio 255 / 256 ký tự", "Đã đăng nhập",
    ["Lưu profile với username dài 2, 3, 30, 31 ký tự", "Lưu bio 255 ký tự", "Lưu bio 256 ký tự"], "len(username)=2,3,30,31; bio='b'*255 ; 'c'*256",
    "Username 2 và 31 bị từ chối, 3 và 30 được chấp nhận; bio lưu tối đa 255 ký tự, không gây lỗi DB",
    "Boundary Value Analysis", "Boundary", "Medium")
def test_prf_04(user, ev):
    suffix = uniq("")[-5:]
    cases = [("q" + suffix[:1], False), ("e" + suffix[:2], True), (("p" * 30)[:25] + suffix, True), (("p" * 31)[:26] + suffix, False)]
    for name, ok in cases:
        r = _save(user, username=name)
        got = "Profile updated" in strip_tags(r.text)
        ev.note(f"len={len(name)} -> {'saved' if got else 'rejected'}")
        assert got == ok, f"len={len(name)}: kỳ vọng {'OK' if ok else 'lỗi'}"
        if got:
            user.username = name
    _save(user, bio="b" * 255)
    assert len(db.scalar("SELECT bio FROM users WHERE id=?", (user.user_id,))) == 255
    r = _save(user, bio="c" * 256)
    n = len(db.scalar("SELECT bio FROM users WHERE id=?", (user.user_id,)))
    ev.note(f"bio 256 ký tự được lưu với độ dài {n}")
    assert r.status_code == 200 and n <= 255 and "SQLSTATE" not in r.text


@tc("TC-PRF-05", "TS-04", "FR-04", "Chọn avatar có sẵn; đường dẫn avatar tuỳ ý bị bỏ qua", "Đã đăng nhập",
    ["Chọn avt_3.jpg", "Gửi avatar_choice = đường dẫn ngoài danh sách"], "/anyn/uploads/avatars/avt_3.jpg | http://evil.test/x.png",
    "Avatar có sẵn được lưu; giá trị ngoài danh sách không được lưu", "Equivalence Partitioning", "Valid", "Medium")
def test_prf_05(user, ev):
    _save(user, avatar_choice="/anyn/uploads/avatars/avt_3.jpg")
    assert db.scalar("SELECT avatar_url FROM users WHERE id=?", (user.user_id,)) == "/anyn/uploads/avatars/avt_3.jpg"
    _save(user, avatar_choice="http://evil.test/x.png")
    now = db.scalar("SELECT avatar_url FROM users WHERE id=?", (user.user_id,))
    ev.note(f"avatar after tampered value: {now}")
    assert now == "/anyn/uploads/avatars/avt_3.jpg"


@tc("TC-PRF-06", "TS-04", "FR-04", "Upload avatar riêng chỉ dành cho người đã chi ≥ $10 (premium)", "Một user total_spent = 0 và một user total_spent = 25",
    ["User thường upload PNG hợp lệ ở mục custom avatar", "User premium upload PNG hợp lệ"], "avatar.png (8×8)",
    "User thường: lỗi 'Nice try! You need to spend $10…', avatar không đổi; premium: lưu thành công, avatar_url trỏ tới file mới và file tồn tại trên đĩa",
    "Decision Table (premium × file)", "Valid", "High")
def test_prf_06(user, premium, ev):
    r = _save(user, _files={"custom_avatar": ("a.png", png(), "image/png")})
    assert "Nice try" in strip_tags(r.text), strip_tags(r.text)[:200]
    assert db.scalar("SELECT avatar_url FROM users WHERE id=?", (user.user_id,)) in (None, "") or "user_" not in db.scalar("SELECT avatar_url FROM users WHERE id=?", (user.user_id,))
    r = _save(premium, _files={"custom_avatar": ("a.png", png(), "image/png")})
    assert "Profile updated" in strip_tags(r.text), strip_tags(r.text)[:200]
    url = db.scalar("SELECT avatar_url FROM users WHERE id=?", (premium.user_id,))
    path = os.path.join(UPLOAD_DIR, "avatars", os.path.basename(url))
    ev.note(f"premium: avatar_url={url}, file exists={os.path.isfile(path)}")
    assert url.startswith("/anyn/uploads/avatars/user_") and os.path.isfile(path)


@tc("TC-PRF-07", "TS-04", "FR-04", "Upload avatar: file giả mạo (PHP đổi đuôi .png) và biên dung lượng 2 MB", "total_spent = 25",
    ["Upload shell.php đặt tên shell.png", "Upload PNG đúng 2.097.152 byte", "Upload PNG 2.097.153 byte"],
    "script PHP; png=2MB; png=2MB+1", "Script bị từ chối; 2 MB được chấp nhận; 2 MB + 1 byte bị từ chối",
    "Boundary Value Analysis + Error Guessing", "Boundary", "High")
def test_prf_07(premium, ev):
    r = _save(premium, _files={"custom_avatar": ("shell.png", PHP_SCRIPT, "image/png")})
    assert "Invalid file type" in strip_tags(r.text), "file PHP giả ảnh được chấp nhận"
    ev.note("php-as-png: rejected")
    r = _save(premium, _files={"custom_avatar": ("big.png", png(pad_to=2 * 1024 * 1024), "image/png")})
    assert "Profile updated" in strip_tags(r.text), "2MB đúng biên bị từ chối: " + strip_tags(r.text)[:100]
    ev.note("exactly 2 MB: accepted")
    r = _save(premium, _files={"custom_avatar": ("big.png", png(pad_to=2 * 1024 * 1024 + 1), "image/png")})
    assert "Invalid file type or too large" in strip_tags(r.text), "2MB+1 được chấp nhận"
    ev.note("2 MB + 1 byte: rejected")


@tc("TC-PRF-08", "TS-04", "FR-04", "Bio chứa mã script được escape khi hiển thị (XSS)", "Đã đăng nhập",
    ["Lưu bio '<script>alert(1)</script><img src=x onerror=alert(2)>'", "Xem Profile và trang member công khai"], "payload XSS",
    "Hiển thị dạng văn bản (&lt;script&gt;), không có thẻ script/onerror thực thi trong HTML", "Error Guessing (security)", "Invalid", "High")
def test_prf_08(user, ev):
    payload = "<script>alert(1)</script><img src=x onerror=alert(2)>"
    _save(user, bio=payload)
    for page in ("profile.php", f"user.php?id={user.user_id}"):
        html = user.get(page, allow_redirects=True).text
        assert "<script>alert(1)</script>" not in html and "<img src=x onerror" not in html, f"XSS thô trên {page}"
        assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html, f"payload không hiển thị dạng escape trên {page}"
        ev.note(f"{page}: payload escaped")


@tc("TC-PRF-09", "TS-04", "FR-04", "Theo dõi / bỏ theo dõi thành viên; không tự theo dõi; khách bị chuyển tới đăng nhập", "Đã đăng nhập, có member khác",
    ["Bấm Follow trên trang bob_qa hai lần", "Bấm Unfollow", "Gửi follow chính mình", "Khách gửi follow"], "target=bob_qa (id 3); target=chính mình",
    "Follow tạo 1 bản ghi (gửi trùng không tạo thêm / không lỗi); Unfollow xoá bản ghi; không tạo bản ghi tự follow; khách được chuyển về login",
    "State Transition Testing + Error Guessing", "Valid", "Medium")
def test_prf_09(user, guest, ev):
    for _ in range(2):
        r = user.post("user.php?id=3", {"follow_action": "follow"})
        assert r.status_code == 302
    n = db.scalar("SELECT COUNT(*) FROM user_follows WHERE follower_id=? AND following_id=3", (user.user_id,))
    ev.note(f"rows after 2×follow: {n}")
    assert n == 1
    user.post("user.php?id=3", {"follow_action": "unfollow"})
    assert db.scalar("SELECT COUNT(*) FROM user_follows WHERE follower_id=? AND following_id=3", (user.user_id,)) == 0
    user.post(f"user.php?id={user.user_id}", {"follow_action": "follow"})
    assert db.scalar("SELECT COUNT(*) FROM user_follows WHERE follower_id=?", (user.user_id,)) == 0, "tự follow được"
    r = guest.post("user.php?id=3", {"follow_action": "follow"}, token_page="login.php")
    ev.http("guest follow", r)
    assert r.status_code == 302 and "login" in r.headers.get("Location", "")


@tc("TC-PRF-10", "TS-04", "FR-04", "Chỉ chủ bài mới xoá được bài cộng đồng của mình (IDOR)", "user A có 1 bài, user B đăng nhập",
    ["B gửi delete_post_id của bài A", "A gửi delete_post_id của chính mình"], "post_id của A",
    "Yêu cầu của B không xoá bài; yêu cầu của A xoá được", "Decision Table (owner × action)", "Invalid", "High")
def test_prf_10(user, user2, ev):
    pid = db.run("INSERT INTO community_posts (user_id,title,image_url,rating,status) VALUES (?,?,?,?,?)",
                 (user.user_id, "idor-test", "/anyn/uploads/avatars/avt_1.jpg", "sfw", "approved"))
    user2.post(f"user.php?id={user.user_id}", {"delete_post_id": pid})
    assert db.scalar("SELECT COUNT(*) FROM community_posts WHERE id=?", (pid,)) == 1, "người khác xoá được bài"
    user.post(f"user.php?id={user.user_id}", {"delete_post_id": pid})
    assert db.scalar("SELECT COUNT(*) FROM community_posts WHERE id=?", (pid,)) == 0, "chủ bài không xoá được"
