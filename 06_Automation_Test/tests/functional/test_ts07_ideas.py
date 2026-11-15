"""TS-07 — Ideas Board: submit / upvote / edit / delete / admin workflow (FR-07)."""
import os

from framework import db, images
from framework.client import strip_tags
from framework.config import UPLOAD_DIR
from framework.tcmeta import tc

MB10 = 10 * 1024 * 1024
FIELDS = dict(title="Ice mage", appearance="Silver hair, pale eyes", context="Frozen kingdom at war")


def submit(c, files=None, **over):
    d = dict(FIELDS)
    d.update(over)
    return c.post("submit_idea.php", d, files=files)


def idea_of(user_id, title=None):
    sql, p = "SELECT * FROM ideas WHERE user_id=?", [user_id]
    if title is not None:
        sql, p = sql + " AND title=?", p + [title]
    return db.q(sql + " ORDER BY id DESC", p)


def make_idea(user_id, status="open", title="Seeded idea"):
    return db.run("INSERT INTO ideas (user_id,title,appearance,context,upvotes,work_status) VALUES (?,?,?,?,0,?)",
                  (user_id, title, "a", "b", status))


def ideas_post(c, data):
    return c.post("ideas.php", data, token_page="ideas.php")


@tc("TC-IDE-01", "TS-07", "FR-07", "Gửi ý tưởng hợp lệ → lưu ý tưởng và thưởng 10 gems",
    "Đã đăng nhập (tài khoản mới, 0 gems)", ["Mở submit_idea.php", "Nhập Title/Appearance/Context hợp lệ", "Gửi"],
    "title='Ice mage'; appearance='Silver hair, pale eyes'; context='Frozen kingdom at war'",
    "Thông báo 'Idea submitted successfully'; 1 bản ghi ideas (work_status=open, upvotes=0); gems = 10",
    "Equivalence Partitioning (valid class) + Use-case testing", "Valid", "High")
def test_ide_01(user, ev):
    r = submit(user)
    ev.http("POST submit_idea", r, strip_tags(r.text)[strip_tags(r.text).find("Idea submitted"):][:60])
    rows = idea_of(user.user_id)
    ev.note(f"ideas rows={len(rows)}, status={rows[0]['work_status'] if rows else None}, gems={db.gems(user.user_id)}")
    assert "Idea submitted successfully" in r.text
    assert len(rows) == 1 and rows[0]["work_status"] == "open" and rows[0]["upvotes"] == 0
    assert db.gems(user.user_id) == 10


@tc("TC-IDE-02", "TS-07", "FR-07", "Bảng quyết định trường bắt buộc (Title × Appearance × Context)",
    "Đã đăng nhập", ["Gửi form với từng tổ hợp thiếu trường"],
    "(rỗng,đủ,đủ) | (đủ,rỗng,đủ) | (đủ,đủ,rỗng) | (toàn khoảng trắng) | (đủ,đủ,đủ)",
    "Thiếu bất kỳ trường nào → 'Please fill in all required fields', không lưu, không thưởng gems; chỉ tổ hợp đủ mới lưu",
    "Decision Table", "Invalid", "High")
def test_ide_02(user, ev):
    combos = [dict(title=""), dict(appearance=""), dict(context=""), dict(title="  ", appearance="\t", context=" \n ")]
    for c in combos:
        r = submit(user, **c)
        ev.note(f"{c} → lỗi hiển thị={'Please fill in all required fields' in r.text}")
        assert "Please fill in all required fields" in r.text
    assert idea_of(user.user_id) == [] and db.gems(user.user_id) == 0
    r = submit(user)
    assert "Idea submitted successfully" in r.text and len(idea_of(user.user_id)) == 1


@tc("TC-IDE-03", "TS-07", "FR-07", "Giá trị biên độ dài: Title 150/151 và Appearance 3000/3001 ký tự",
    "Đã đăng nhập", ["Gửi Title dài 150 → 151", "Gửi Appearance dài 3000 → 3001"], "150 | 151 | 3000 | 3001 ký tự 'a'",
    "Giá trị ≤ giới hạn lưu nguyên; vượt giới hạn bị cắt về đúng giới hạn (không lỗi 500, không lưu quá dài)",
    "Boundary Value Analysis", "Boundary", "Medium")
def test_ide_03(user, ev):
    cases = [("title", 150, 150), ("title", 151, 150), ("appearance", 3000, 3000), ("appearance", 3001, 3000)]
    for field, n, expect in cases:
        before = len(idea_of(user.user_id))
        r = submit(user, **{field: "a" * n})
        assert r.status_code == 200
        row = idea_of(user.user_id)[0]
        stored = len(row[field])
        ev.note(f"{field}={n} ký tự → lưu {stored} ký tự (mong đợi {expect})")
        assert len(idea_of(user.user_id)) == before + 1 and stored == expect


@tc("TC-IDE-04", "TS-07", "FR-07", "Kiểm tra liên kết ảnh: chỉ chấp nhận http(s)",
    "Đã đăng nhập", ["Gửi image_url với từng giá trị"],
    "javascript:alert(1) | ftp://x/y.png | data:image/png;base64,AAAA | 'khong phai url' | https://example.com/a.png",
    "4 giá trị đầu bị từ chối 'Image link must be a valid http(s) URL' và không lưu; https hợp lệ được lưu",
    "Equivalence Partitioning (scheme classes)", "Invalid", "High")
def test_ide_04(user, ev):
    for bad in ["javascript:alert(1)", "ftp://example.com/y.png", "data:image/png;base64,AAAA", "khong phai url"]:
        r = submit(user, image_url=bad)
        ev.note(f"image_url={bad!r} → bị từ chối={'valid http(s) URL' in r.text}")
        assert "Image link must be a valid http(s) URL" in r.text
    assert idea_of(user.user_id) == []
    r = submit(user, image_url="https://example.com/a.png")
    assert "Idea submitted successfully" in r.text
    assert idea_of(user.user_id)[0]["image_url"] == "https://example.com/a.png"


@tc("TC-IDE-05", "TS-07", "FR-07", "Tải ảnh lên: PNG hợp lệ được nhận; mã PHP/HTML đội lốt ảnh bị từ chối; biên 10 MB",
    "Đã đăng nhập", ["Tải PNG thật", "Tải file .png chứa mã PHP", "Tải file .php", "Tải PNG đúng 10 MB và 10 MB + 1 byte"],
    "png 8x8 | <?php…?> đặt tên .png | .php | 10 485 760 B | 10 485 761 B",
    "PNG thật lưu vào /anyn/uploads/<ts>_idea_<random>.png (file tồn tại); file mã độc & 10MB+1 bị từ chối; đúng 10 MB được chấp nhận",
    "Equivalence Partitioning + Boundary Value Analysis + Error Guessing", "Boundary", "High")
def test_ide_05(user, ev):
    r = submit(user, files={"idea_image_file": ("pic.png", images.png(), "image/png")})
    row = idea_of(user.user_id)[0]
    path = os.path.join(UPLOAD_DIR, os.path.basename(row["image_url"]))
    ev.note(f"PNG thật → {row['image_url']} (tồn tại={os.path.isfile(path)})")
    assert "Idea submitted successfully" in r.text and row["image_url"].startswith("/anyn/uploads/") and row["image_url"].endswith(".png")
    assert os.path.isfile(path)
    n = len(idea_of(user.user_id))
    for name, body in [("shell.png", images.PHP_SCRIPT), ("shell.php", images.PHP_SCRIPT), ("x.png", images.HTML_SCRIPT)]:
        r = submit(user, files={"idea_image_file": (name, body, "image/png")})
        ev.note(f"upload {name} ({len(body)} B) → từ chối={'Invalid image format' in r.text}")
        assert "Invalid image format" in r.text
    assert len(idea_of(user.user_id)) == n
    r = submit(user, files={"idea_image_file": ("big.png", images.png(pad_to=MB10), "image/png")})
    ev.note(f"đúng 10 MB → chấp nhận={'Idea submitted successfully' in r.text}")
    assert "Idea submitted successfully" in r.text
    r = submit(user, files={"idea_image_file": ("big2.png", images.png(pad_to=MB10 + 1), "image/png")})
    ev.note(f"10 MB + 1 → từ chối={'Invalid image format' in r.text}")
    assert "Invalid image format" in r.text


@tc("TC-IDE-06", "TS-07", "FR-07", "Bình chọn (upvote): mỗi người một lần; khách bị chặn; chỉ ý tưởng 'open'",
    "Ý tưởng open của alice (id=1) và ý tưởng in_progress (id=2)", ["User upvote ý tưởng 1 hai lần", "Khách upvote", "User upvote ý tưởng in_progress"],
    "idea 1 | idea 2", "Lần 1: upvotes +1 và +1 gem; lần 2: không đổi; khách → ?error=login; ý tưởng in_progress → không đổi",
    "State Transition + Decision Table (role × state)", "Valid", "High")
def test_ide_06(user, guest, ev):
    iid = make_idea(db.scalar("SELECT id FROM users WHERE username='alice_qa'"))
    base = db.scalar("SELECT upvotes FROM ideas WHERE id=?", (iid,))
    ideas_post(user, {"upvote_id": iid})
    ideas_post(user, {"upvote_id": iid})
    up = db.scalar("SELECT upvotes FROM ideas WHERE id=?", (iid,))
    ev.note(f"upvote 2 lần: upvotes {base}→{up}, gems={db.gems(user.user_id)}")
    assert up == base + 1 and db.gems(user.user_id) == 1
    r = guest.post("ideas.php", {"upvote_id": iid}, token_page="login.php")
    ev.http("guest upvote", r)
    assert "error=login" in r.headers.get("Location", "") and db.scalar("SELECT upvotes FROM ideas WHERE id=?", (iid,)) == up
    prog = make_idea(db.scalar("SELECT id FROM users WHERE username='bob_qa'"), status="in_progress")
    ideas_post(user, {"upvote_id": prog})
    assert db.scalar("SELECT upvotes FROM ideas WHERE id=?", (prog,)) == 0


@tc("TC-IDE-07", "TS-07", "FR-07", "Phân quyền sửa/xoá ý tưởng: chủ sở hữu + trạng thái open",
    "alice có ý tưởng open và in_progress; user khác", ["Chủ sở hữu sửa ý tưởng open", "User khác sửa/xoá", "Chủ sở hữu sửa/xoá ý tưởng in_progress", "Chủ sở hữu xoá ý tưởng open"],
    "edit_idea.php?id=N, delete_idea_id=N", "Chỉ chủ sở hữu + open được sửa/xoá; còn lại bị chuyển về ?error=forbidden và dữ liệu không đổi; xoá kèm xoá idea_upvotes",
    "Decision Table (owner × status)", "Invalid", "High")
def test_ide_07(user, user2, ev):
    mine = make_idea(user.user_id, title="mine-open")
    prog = make_idea(user.user_id, status="in_progress", title="mine-progress")
    r = user.post(f"edit_idea.php?id={mine}", dict(FIELDS, title="mine-open-EDITED"))
    ev.http("owner edit (open)", r)
    assert r.status_code == 302 and "msg=updated" in r.headers["Location"]
    assert db.scalar("SELECT title FROM ideas WHERE id=?", (mine,)) == "mine-open-EDITED"
    r = user2.get(f"edit_idea.php?id={mine}")
    ev.http("other user opens edit page", r)
    assert "error=forbidden" in r.headers.get("Location", "")
    ideas_post(user2, {"delete_idea_id": mine})
    assert db.scalar("SELECT COUNT(*) FROM ideas WHERE id=?", (mine,)) == 1
    r = user.get(f"edit_idea.php?id={prog}")
    assert "error=forbidden" in r.headers.get("Location", "")
    ideas_post(user, {"delete_idea_id": prog})
    assert db.scalar("SELECT COUNT(*) FROM ideas WHERE id=?", (prog,)) == 1
    db.run("INSERT OR IGNORE INTO idea_upvotes (user_id, idea_id) VALUES (?,?)", (user2.user_id, mine))
    r = ideas_post(user, {"delete_idea_id": mine})
    ev.http("owner delete (open)", r)
    assert "msg=deleted" in r.headers.get("Location", "")
    assert db.scalar("SELECT COUNT(*) FROM ideas WHERE id=?", (mine,)) == 0
    assert db.scalar("SELECT COUNT(*) FROM idea_upvotes WHERE idea_id=?", (mine,)) == 0


@tc("TC-IDE-08", "TS-07", "FR-07", "Vòng đời ý tưởng do admin điều khiển: open → in_progress → completed → reopen; người dùng thường không thể",
    "Ý tưởng open; tài khoản admin và user thường", ["User thường gửi idea_set_progress", "Admin: idea_set_progress", "Admin: idea_complete (published, bot_id=3)", "Admin: idea_reopen"],
    "idea_set_progress / idea_complete / idea_reopen", "User thường: không đổi; admin: open→in_progress→completed(bot_id=3, published)→open (bot_id, completed_at = NULL)",
    "State Transition Testing", "Valid", "High")
def test_ide_08(user, admin, ev):
    iid = make_idea(user.user_id)
    ideas_post(user, {"idea_set_progress": "1", "idea_id": iid})
    st = lambda: db.one("SELECT work_status, bot_id, bot_visibility, completed_at FROM ideas WHERE id=?", (iid,))
    ev.note(f"user thường → {st()['work_status']}")
    assert st()["work_status"] == "open"
    ideas_post(admin, {"idea_set_progress": "1", "idea_id": iid})
    assert st()["work_status"] == "in_progress"
    ideas_post(admin, {"idea_complete": "1", "idea_id": iid, "bot_id": 3, "bot_visibility": "published"})
    s = st()
    ev.note(f"completed → {s}")
    assert s["work_status"] == "completed" and s["bot_id"] == 3 and s["bot_visibility"] == "published" and s["completed_at"]
    ideas_post(admin, {"idea_reopen": "1", "idea_id": iid})
    s = st()
    ev.note(f"reopen → {s}")
    assert s["work_status"] == "open" and s["bot_id"] is None and s["completed_at"] is None


@tc("TC-IDE-09", "TS-07", "FR-07", "Hoàn thành dạng 'unlisted': bắt buộc có liên kết và liên kết phải là http(s)",
    "Admin; ý tưởng in_progress", ["Hoàn thành unlisted không có link", "Hoàn thành unlisted với link javascript:alert(1)", "Mở trang Ideas bằng tài khoản chủ ý tưởng"],
    "unlisted_link = '' | 'javascript:alert(1)'", "Thiếu link → ?error=link_required, không đổi. Link không phải http(s) phải bị từ chối; không được xuất hiện trong href cho người dùng",
    "Error Guessing (security) + Decision Table", "Invalid", "Medium", bug=["BUG-005"])
def test_ide_09(user, admin, ev):
    iid = make_idea(user.user_id, status="in_progress")
    r = ideas_post(admin, {"idea_complete": "1", "idea_id": iid, "bot_visibility": "unlisted", "unlisted_link": ""})
    ev.http("unlisted không có link", r)
    assert "error=link_required" in r.headers.get("Location", "")
    assert db.scalar("SELECT work_status FROM ideas WHERE id=?", (iid,)) == "in_progress"
    ideas_post(admin, {"idea_complete": "1", "idea_id": iid, "bot_visibility": "unlisted", "unlisted_link": "javascript:alert(1)"})
    stored = db.one("SELECT work_status, unlisted_link FROM ideas WHERE id=?", (iid,))
    page = user.get("ideas.php", allow_redirects=True).text
    in_href = 'href="javascript:alert(1)"' in page
    ev.note(f"DB: {stored}; xuất hiện trong thẻ <a href> của chủ ý tưởng: {in_href}")
    assert not in_href and stored["unlisted_link"] != "javascript:alert(1)", \
        "liên kết 'javascript:' do admin nhập được lưu và render thành href cho người dùng (không kiểm tra scheme)"
