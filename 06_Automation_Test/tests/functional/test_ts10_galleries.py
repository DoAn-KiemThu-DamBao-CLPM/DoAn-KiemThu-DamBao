"""TS-10 — Official gallery & community gallery: browsing, reactions, uploads (FR-10)."""
import os

from framework import db, images
from framework.client import strip_tags
from framework.config import UPLOAD_DIR
from framework.tcmeta import tc

GID = 5           # seeded official artwork "Seed art 5"
POST_OK = 1       # seeded approved community post (alice)
POST_PENDING = 3  # seeded pending community post (bob)


def g_react(c, gid, typ, token_page="gallery.php"):
    d = {"react": "1", "gallery_id": gid}
    if typ is not None:
        d["reaction_type"] = typ
    return c.post("gallery.php", d, token_page=token_page)


def c_react(c, pid, typ, token_page="community_gallery.php"):
    return c.post("community_gallery.php", {"react": "1", "post_id": pid, "reaction_type": typ}, token_page=token_page)


def g_row(uid, gid=GID):
    return db.one("SELECT reaction_type FROM gallery_reactions WHERE user_id=? AND gallery_id=?", (uid, gid))


def c_row(uid, pid):
    return db.one("SELECT reaction_type FROM community_reactions WHERE user_id=? AND post_id=?", (uid, pid))


@tc("TC-GAL-01", "TS-10", "FR-10", "Xem Official Gallery như khách; khách bấm reaction bị yêu cầu đăng nhập",
    "Chưa đăng nhập; gallery có 12 ảnh + 1 bộ sưu tập", ["Mở gallery.php", "Gửi POST react (like) khi chưa đăng nhập"],
    "gallery_id=5; reaction_type=like", "Trang hiển thị (HTTP 200) có tiêu đề ảnh seed; reaction của khách → chuyển ?error=login, không có bản ghi gallery_reactions",
    "Equivalence Partitioning (role) + Use-case testing", "Valid", "Medium")
def test_gal_01(guest, ev):
    r = guest.get("gallery.php")
    ev.http("GET gallery.php (guest)", r)
    assert r.status_code == 200 and "Seed art" in r.text
    r = g_react(guest, GID, "like", token_page="login.php")
    ev.http("guest react", r)
    assert "error=login" in r.headers.get("Location", "")
    assert db.scalar("SELECT COUNT(*) FROM gallery_reactions WHERE gallery_id=?", (GID,)) == 0


@tc("TC-GAL-02", "TS-10", "FR-10", "Vòng đời reaction trên Official Gallery: thêm → đổi loại → bấm lại để gỡ (mỗi người 1 reaction/ảnh)",
    "Đã đăng nhập (0 gems), chưa có reaction", ["Bấm like", "Bấm fire (đổi)", "Bấm fire lần nữa (gỡ)"],
    "like → fire → fire", "Sau từng bước: like (+2 gems) → fire (vẫn 1 bản ghi, không +gems) → không còn bản ghi",
    "State Transition Testing", "Valid", "High")
def test_gal_02(user, ev):
    g_react(user, GID, "like")
    s1, gem1 = g_row(user.user_id), db.gems(user.user_id)
    g_react(user, GID, "fire")
    s2, gem2 = g_row(user.user_id), db.gems(user.user_id)
    g_react(user, GID, "fire")
    s3 = g_row(user.user_id)
    ev.note(f"like→{s1}, gems={gem1}; fire→{s2}, gems={gem2}; fire lần 2→{s3}")
    assert s1 and s1["reaction_type"] == "like" and gem1 == 2
    assert s2 and s2["reaction_type"] == "fire" and gem2 == 2
    assert s3 is None
    assert db.scalar("SELECT COUNT(*) FROM gallery_reactions WHERE user_id=?", (user.user_id,)) == 0


@tc("TC-GAL-03", "TS-10", "FR-10", "Loại reaction không hợp lệ bị bỏ qua (Community) và Official Gallery cũng phải kiểm tra tương tự",
    "Đã đăng nhập", ["Gửi reaction_type='hack' và '' lên Community Gallery", "Gửi reaction_type='hack' và '' lên Official Gallery"],
    "reaction_type ∈ {hack, ''} (hợp lệ: like|love|fire)", "Không tạo bản ghi, không cộng gems, không lỗi PHP/Fatal; phản hồi chuyển hướng về trang gallery",
    "Equivalence Partitioning (invalid class) + Error Guessing", "Invalid", "Medium", bug=["BUG-011"])
def test_gal_03(user, ev):
    for typ in ("hack", ""):
        r = c_react(user, POST_OK, typ)
        ev.note(f"community type={typ!r} → HTTP {r.status_code}, bản ghi={c_row(user.user_id, POST_OK)}")
        assert r.status_code == 302 and c_row(user.user_id, POST_OK) is None
    assert db.gems(user.user_id) == 0
    problems = []
    for typ in ("hack", ""):
        r = g_react(user, GID, typ)
        fatal = "Fatal error" in r.text or "Uncaught" in r.text
        row = g_row(user.user_id)
        ev.note(f"official type={typ!r} → HTTP {r.status_code}, fatal={fatal}, bản ghi={row}, gems={db.gems(user.user_id)}")
        if fatal or row or db.gems(user.user_id):
            problems.append((typ, fatal, row))
        db.run("DELETE FROM gallery_reactions WHERE user_id=?", (user.user_id,))
    assert not problems, f"Official Gallery không kiểm tra reaction_type: {problems}"


@tc("TC-GAL-04", "TS-10", "FR-10", "Reaction lên ảnh/bài không tồn tại hoặc chưa duyệt không được tạo dữ liệu và không được thưởng gems",
    "Đã đăng nhập (0 gems); gallery_id 999999 không tồn tại; bài community #3 đang pending", ["React like gallery_id=999999", "React like post_id=999999", "React like post_id=3 (pending)"],
    "gallery 999999 | community 999999 | community 3 (pending)", "Không có bản ghi reaction mới và gems vẫn = 0 cho cả 3 trường hợp",
    "Error Guessing (parameter tampering)", "Invalid", "Medium", bug=["BUG-012"])
def test_gal_04(user, ev):
    g_react(user, 999999, "like")
    c_react(user, 999999, "like")
    c_react(user, POST_PENDING, "like")
    rows = (db.scalar("SELECT COUNT(*) FROM gallery_reactions WHERE user_id=?", (user.user_id,)),
            db.scalar("SELECT COUNT(*) FROM community_reactions WHERE user_id=?", (user.user_id,)))
    ev.note(f"bản ghi tạo ra (gallery, community) = {rows}; gems = {db.gems(user.user_id)}")
    assert rows == (0, 0) and db.gems(user.user_id) == 0, \
        f"reaction lên đối tượng không tồn tại/chưa duyệt vẫn được lưu {rows} và thưởng {db.gems(user.user_id)} gems"


@tc("TC-GAL-05", "TS-10", "FR-10", "Tải tranh lên Community: kiểm tra điều kiện, chờ duyệt, thưởng 15 gems tối đa 2 lần/ngày",
    "Đã đăng nhập (0 gems)", ["Gửi không tick guideline", "Gửi không chọn ảnh", "Gửi file PHP đội lốt .png", "Gửi PNG hợp lệ ×3"],
    "agree_guidelines | image_file", "3 trường hợp đầu bị từ chối đúng thông báo; PNG hợp lệ → bài 'pending' (chưa hiển thị công khai); gems: +15, +15, lần 3: +0",
    "Decision Table + Boundary Value Analysis (cap 2/3)", "Boundary", "High")
def test_gal_05(user, guest, ev):
    def up(files=None, agree=True, title="QA art"):
        d = {"submit_community": "1", "title": title}
        if agree:
            d["agree_guidelines"] = "1"
        return user.post("community_upload.php", d, files=files, token_page="community_upload.php")
    png = lambda: {"image_file": ("a.png", images.png(), "image/png")}
    assert "accept the Community Guidelines" in up(png(), agree=False).text
    assert "select an image" in up(None).text
    assert "Invalid file or upload failed" in up({"image_file": ("a.png", images.PHP_SCRIPT, "image/png")}).text
    assert db.scalar("SELECT COUNT(*) FROM community_posts WHERE user_id=?", (user.user_id,)) == 0
    for i in range(3):
        r = up(png(), title=f"QA art {i}")
        ev.http(f"upload #{i + 1}", r)
        assert r.status_code == 302 and "msg=submitted" in r.headers["Location"]
    posts = db.q("SELECT * FROM community_posts WHERE user_id=?", (user.user_id,))
    ev.note(f"bài tạo ra={len(posts)}, trạng thái={set(p['status'] for p in posts)}, gems={db.gems(user.user_id)} (mong đợi 30)")
    assert len(posts) == 3 and {p["status"] for p in posts} == {"pending"} and db.gems(user.user_id) == 30
    assert os.path.isfile(os.path.join(UPLOAD_DIR, "community", os.path.basename(posts[0]["image_url"])))
    assert "QA art 0" not in guest.get("community_gallery.php").text


@tc("TC-GAL-06", "TS-10", "FR-10", "Community Gallery chỉ hiển thị bài đã duyệt; chủ bài thấy số bài chờ duyệt và lý do bị từ chối",
    "Seed: 2 bài approved (alice), 1 pending + 1 rejected 'Too dark' (bob)", ["Khách xem community_gallery.php", "Đăng nhập bob và xem lại"],
    "bob_qa", "Khách: thấy 2 bài approved, không thấy pending/rejected; bob: thấy thông báo 1 bài chờ duyệt và 'Reason: Too dark'",
    "Decision Table (role × status)", "Valid", "High")
def test_gal_06(guest, bob, ev):
    page = strip_tags(guest.get("community_gallery.php").text)
    ev.note(f"khách: approved={('Alice approved art' in page)}, pending={('Bob pending art' in page)}, rejected={('Bob rejected art' in page)}")
    assert "Alice approved art" in page and "Bob pending art" not in page and "Bob rejected art" not in page.replace("Reason", "")
    mine = strip_tags(bob.get("community_gallery.php").text)
    ev.note(f"bob: 'waiting for admin approval'={'waiting for admin approval' in mine}, 'Too dark'={'Too dark' in mine}")
    assert "waiting for admin approval" in mine and "Too dark" in mine and "Bob pending art" not in mine
