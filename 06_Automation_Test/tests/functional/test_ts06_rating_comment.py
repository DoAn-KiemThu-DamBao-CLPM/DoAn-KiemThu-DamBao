"""TS-06 — Character detail: rating & comments (FR-06)."""
from framework import db
from framework.client import AnynClient, strip_tags
from framework.tcmeta import tc


def rate(c, bot, score):
    d = {"submit_rating": "1"}
    if score is not None:
        d["score"] = score
    return c.post(f"bot_detail.php?id={bot}", d)


def comment(c, bot, text):
    return c.post(f"bot_detail.php?id={bot}", {"submit_comment": "1", "content": text})


def avg(bot):
    return float(db.scalar("SELECT total_rating FROM bots WHERE id=?", (bot,)))


@tc("TC-RAT-01", "TS-06", "FR-06", "Chấm điểm nhân vật lần đầu", "Đã đăng nhập; bot 10 chưa có đánh giá",
    ["Mở bot_detail.php?id=10", "Chọn 5 sao và gửi"], "score=5", "Có 1 bản ghi ratings; bots.total_rating = 5.00", "Equivalence Partitioning (valid class)", "Valid", "High")
def test_rat_01(user, ev):
    db.run("DELETE FROM ratings WHERE bot_id=10")
    r = rate(user, 10, 5)
    assert r.status_code == 302
    assert db.scalar("SELECT COUNT(*) FROM ratings WHERE bot_id=10 AND user_id=?", (user.user_id,)) == 1
    ev.note(f"total_rating bot 10 = {avg(10)}")
    assert avg(10) == 5.0


@tc("TC-RAT-02", "TS-06", "FR-06", "Đổi điểm đánh giá không tạo bản ghi thứ hai; điểm trung bình nhiều người dùng", "bot 11, 12 chưa có đánh giá",
    ["Chấm 5 sao rồi chấm lại 2 sao (cùng user)", "User A chấm 5, user B chấm 2 cho bot khác"], "5 → 2 ; 5 và 2",
    "Vẫn 1 bản ghi, score = 2, total_rating = 2.00; với hai user total_rating = 3.50", "State Transition Testing + Equivalence Partitioning", "Valid", "High")
def test_rat_02(user, user2, ev):
    db.run("DELETE FROM ratings WHERE bot_id IN (11, 12)")
    rate(user, 11, 5)
    rate(user, 11, 2)
    rows = db.q("SELECT score FROM ratings WHERE bot_id=11 AND user_id=?", (user.user_id,))
    ev.note(f"đổi điểm: rows={rows}, avg={avg(11)}")
    assert len(rows) == 1 and rows[0]["score"] == 2 and avg(11) == 2.0
    rate(user, 12, 5)
    rate(user2, 12, 2)
    ev.note(f"hai người dùng: avg={avg(12)}")
    assert avg(12) == 3.5


@tc("TC-RAT-03", "TS-06", "FR-06", "Điểm ngoài khoảng 1–5 bị kẹp về biên (0→1, 6→5, 99→5)", "Đã đăng nhập",
    ["Gửi score=0, 6, 99, -3"], "0 | 6 | 99 | -3", "Giá trị được kẹp về [1,5] (hành vi thiết kế), không lỗi", "Boundary Value Analysis", "Boundary", "Medium")
def test_rat_03(user, ev):
    db.run("DELETE FROM ratings WHERE bot_id=13")
    for sent, exp in [(0, 1), (6, 5), (99, 5), (-3, 1)]:
        rate(user, 13, sent)
        got = db.scalar("SELECT score FROM ratings WHERE bot_id=13 AND user_id=?", (user.user_id,))
        ev.note(f"score={sent} → lưu {got}")
        assert got == exp


@tc("TC-RAT-04", "TS-06", "FR-06", "Điểm thiếu hoặc không phải số phải bị từ chối, không được lưu thành 1 sao", "Đã đăng nhập",
    ["Gửi submit_rating không có score", "Gửi score='abc'"], "(thiếu) | abc",
    "Không tạo/sửa bản ghi ratings (hoặc báo lỗi hợp lệ); không có PHP Warning", "Error Guessing", "Invalid", "Low", bug=["BUG-004"])
def test_rat_04(user, ev):
    db.run("DELETE FROM ratings WHERE bot_id=14")
    r1 = rate(user, 14, None)
    r2 = rate(user, 14, "abc")
    n = db.scalar("SELECT COUNT(*) FROM ratings WHERE bot_id=14 AND user_id=?", (user.user_id,))
    sc = db.scalar("SELECT score FROM ratings WHERE bot_id=14 AND user_id=?", (user.user_id,))
    ev.note(f"sau khi gửi dữ liệu không hợp lệ: số bản ghi={n}, score={sc}; HTTP {r1.status_code}/{r2.status_code}")
    assert n == 0, f"dữ liệu không hợp lệ bị lưu thành đánh giá {sc} sao"


@tc("TC-RAT-05", "TS-06", "FR-06", "Khách không thể chấm điểm hoặc bình luận", "Chưa đăng nhập", ["Gửi POST submit_rating khi chưa đăng nhập", "Gửi POST submit_comment khi chưa đăng nhập"],
    "score=5 ; content='spam'", "Không có bản ghi ratings/comments mới; điểm trung bình không đổi", "Decision Table (role × action)", "Invalid", "High")
def test_rat_05(guest, ev):
    db.run("DELETE FROM ratings WHERE bot_id=15")
    before = avg(15)
    rate(guest, 15, 5)
    assert db.scalar("SELECT COUNT(*) FROM ratings WHERE bot_id=15") == 0 and avg(15) == before
    n = db.scalar("SELECT COUNT(*) FROM comments")
    guest.post("bot_detail.php?id=28", {"submit_comment": "1", "content": "spam"})
    assert db.scalar("SELECT COUNT(*) FROM comments") == n


@tc("TC-CMT-01", "TS-06", "FR-06", "Đăng bình luận hợp lệ (có tiếng Việt, emoji)", "Đã đăng nhập", ["Nhập bình luận", "Gửi"],
    "'Nhân vật rất hay! 😍'", "Bình luận hiển thị ở đầu danh sách với tên người dùng; lưu đúng UTF-8", "Equivalence Partitioning", "Valid", "High")
def test_cmt_01(user, ev):
    text = "Nhân vật rất hay! 😍"
    r = comment(user, 20, text)
    assert r.status_code == 302
    page = user.get("bot_detail.php?id=20", allow_redirects=True).text
    assert text in page and user.username in page


@tc("TC-CMT-02", "TS-06", "FR-06", "Bình luận rỗng/chỉ khoảng trắng không được lưu; độ dài tại biên 1000 ký tự", "Đã đăng nhập",
    ["Gửi '', '    ', '\\n\\t '", "Gửi 1, 1000, 1001 ký tự"], "'' | '    ' | len=1, 1000, 1001",
    "Rỗng/khoảng trắng: không tạo bản ghi; 1 và 1000 lưu nguyên; 1001 bị cắt còn 1000 (không lỗi DB)", "Equivalence Partitioning (invalid class) + Boundary Value Analysis", "Boundary", "Medium")
def test_cmt_02(user, ev):
    for t in ("", "    ", "\n\t "):
        comment(user, 21, t)
    assert db.scalar("SELECT COUNT(*) FROM comments WHERE user_id=?", (user.user_id,)) == 0
    for n in (1, 1000, 1001):
        comment(user, 22, "k" * n)
    lens = sorted(len(r["content"]) for r in db.q("SELECT content FROM comments WHERE user_id=?", (user.user_id,)))
    ev.note(f"độ dài đã lưu: {lens}")
    assert lens == [1, 1000, 1000]


@tc("TC-CMT-03", "TS-06", "FR-06", "Bình luận chứa HTML/JS được escape (XSS lưu trữ)", "Đã đăng nhập", ["Gửi bình luận chứa thẻ script/img onerror/svg"],
    "<script>alert(1)</script><img src=x onerror=alert(2)><svg onload=alert(3)>", "HTML hiển thị dạng văn bản đã escape; không có thẻ thực thi", "Error Guessing (security)", "Invalid", "High")
def test_cmt_03(user, guest, ev):
    payload = "<script>alert(1)</script><img src=x onerror=alert(2)><svg onload=alert(3)>"
    comment(user, 23, payload)
    html = guest.get("bot_detail.php?id=23", allow_redirects=True).text
    assert "<script>alert(1)</script>" not in html and "<img src=x onerror" not in html and "<svg onload" not in html
    assert "&lt;script&gt;" in html


@tc("TC-CMT-04", "TS-06", "FR-06", "Chủ bình luận chỉnh sửa và xoá bình luận của mình", "Có bình luận của user", ["Gửi edit_comment với nội dung mới", "Gửi delete_comment"], "new='Đã sửa'",
    "Nội dung cập nhật, edited_at được ghi; sau đó bản ghi bị xoá", "Equivalence Partitioning", "Valid", "Medium")
def test_cmt_04(user, ev):
    comment(user, 24, "bản gốc")
    cid = db.scalar("SELECT id FROM comments WHERE user_id=? ORDER BY id DESC", (user.user_id,))
    user.post("bot_detail.php?id=24", {"edit_comment": "1", "comment_id": cid, "content": "Đã sửa"})
    row = db.one("SELECT content, edited_at FROM comments WHERE id=?", (cid,))
    ev.note(f"{row}")
    assert row["content"] == "Đã sửa" and row["edited_at"]
    user.post("bot_detail.php?id=24", {"delete_comment": "1", "comment_id": cid})
    assert db.scalar("SELECT COUNT(*) FROM comments WHERE id=?", (cid,)) == 0


@tc("TC-CMT-05", "TS-06", "FR-06", "Người khác không sửa/xoá được bình luận của bạn; không thao tác chéo bot qua URL sai (IDOR)", "Bình luận của A thuộc bot 25; B đăng nhập",
    ["B gửi edit_comment và delete_comment", "A gửi delete_comment tới bot_detail.php?id=30 (sai bot)"], "comment_id của A",
    "Bình luận của A giữ nguyên trong cả hai trường hợp", "Decision Table (owner × action) + Error Guessing", "Invalid", "High")
def test_cmt_05(user, user2, ev):
    comment(user, 25, "của A")
    cid = db.scalar("SELECT id FROM comments WHERE user_id=?", (user.user_id,))
    user2.post("bot_detail.php?id=25", {"edit_comment": "1", "comment_id": cid, "content": "hacked"})
    user2.post("bot_detail.php?id=25", {"delete_comment": "1", "comment_id": cid})
    assert db.scalar("SELECT content FROM comments WHERE id=?", (cid,)) == "của A"
    user.post("bot_detail.php?id=30", {"delete_comment": "1", "comment_id": cid})
    assert db.scalar("SELECT COUNT(*) FROM comments WHERE id=?", (cid,)) == 1, "xoá được bình luận qua URL của bot khác"


@tc("TC-CMT-06", "TS-06", "FR-06", "Admin xoá được bình luận của người khác nhưng không sửa được", "Bình luận của user; admin đăng nhập",
    ["Admin gửi edit_comment", "Admin gửi delete_comment"], "comment_id của user", "Sửa bị từ chối (nội dung giữ nguyên); xoá thành công", "Decision Table (role × action)", "Valid", "Medium")
def test_cmt_06(user, admin, ev):
    comment(user, 27, "nội dung gốc")
    cid = db.scalar("SELECT id FROM comments WHERE user_id=?", (user.user_id,))
    admin.post("bot_detail.php?id=27", {"edit_comment": "1", "comment_id": cid, "content": "admin sửa"})
    assert db.scalar("SELECT content FROM comments WHERE id=?", (cid,)) == "nội dung gốc"
    admin.post("bot_detail.php?id=27", {"delete_comment": "1", "comment_id": cid})
    assert db.scalar("SELECT COUNT(*) FROM comments WHERE id=?", (cid,)) == 0
