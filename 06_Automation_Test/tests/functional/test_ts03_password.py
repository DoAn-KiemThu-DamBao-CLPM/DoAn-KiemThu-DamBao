"""TS-03 — Forgot / reset / change password (FR-03)."""
import re

from framework import db
from framework.client import AnynClient, strip_tags, uniq
from framework.tcmeta import tc

SENT = "a reset link has been sent"


def _forgot(c, email):
    return c.post("forgot_password.php", {"email": email})


def _link(r):
    m = re.search(r'href="([^"]*reset_password\.php\?token=([a-f0-9]{64}))"', r.text)
    return (m.group(1), m.group(2)) if m else (None, None)


def _token_for(guest, user):
    """Obtain a valid reset token. If the app shows the dev link, use it; otherwise (production-like build, mail
    not readable by the tester) plant a known token hash for this user, exactly like the app would store it."""
    import hashlib
    r = _forgot(guest, user.email)
    _, tok = _link(r)
    if tok:
        return tok
    tok = "a1" * 32
    db.run("DELETE FROM password_resets WHERE user_id=?", (user.user_id,))
    db.run("INSERT INTO password_resets (user_id, token_hash, expires_at) VALUES (?,?,datetime('now','+30 minutes'))",
           (user.user_id, hashlib.sha256(tok.encode()).hexdigest()))
    return tok


@tc("TC-PWD-01", "TS-03", "FR-03", "Yêu cầu đặt lại mật khẩu với email đã đăng ký", "Có tài khoản",
    ["Mở Forgot password", "Nhập email đã đăng ký", "Gửi"], "email của user mới tạo",
    "Thông báo trung tính 'If that email is registered, a reset link has been sent'; DB có token băm SHA-256 (không lưu token thô), hết hạn sau 30 phút",
    "Equivalence Partitioning (valid class)", "Valid", "High")
def test_pwd_01(user, guest, ev):
    r = _forgot(guest, user.email)
    assert SENT in strip_tags(r.text), strip_tags(r.text)[:150]
    row = db.one("SELECT * FROM password_resets WHERE user_id=?", (user.user_id,))
    assert row and len(row["token_hash"]) == 64, "không có bản ghi token"
    _, tok = _link(r)
    assert tok is None or row["token_hash"] != tok, "token lưu dạng thô"
    ev.note(f"password_resets: expires_at={row['expires_at']}, token_hash={row['token_hash'][:12]}…")


@tc("TC-PWD-02", "TS-03", "FR-03", "Forgot password với email chưa đăng ký (chống dò tài khoản) hoặc sai định dạng", "—",
    ["Gửi Forgot password với email không tồn tại", "Gửi email 'abc'"], "nobody@nowhere.test | abc",
    "Email không tồn tại: thông báo giống hệt trường hợp email tồn tại, không lộ liên kết; email sai định dạng: lỗi 'Please enter a valid email address.'",
    "Equivalence Partitioning (invalid classes) + Error Guessing", "Invalid", "Medium")
def test_pwd_02(guest, ev):
    r = _forgot(guest, f"{uniq('no')}@nowhere.test")
    assert SENT in strip_tags(r.text)
    assert "open reset link" not in r.text, "lộ liên kết cho email không tồn tại"
    assert "valid email" in strip_tags(_forgot(guest, "abc").text)


@tc("TC-PWD-03", "TS-03", "FR-03", "Đặt lại mật khẩu bằng liên kết hợp lệ (luồng đầy đủ)", "Có tài khoản và token hợp lệ",
    ["Yêu cầu reset", "Mở liên kết trong email", "Nhập mật khẩu mới + xác nhận", "Đăng nhập bằng mật khẩu mới và mật khẩu cũ"],
    "new=NewPassw0rd!", "Đổi thành công (redirect login?reset=ok); mật khẩu mới đăng nhập được, mật khẩu cũ bị từ chối",
    "Use-case testing", "Valid", "High")
def test_pwd_03(user, guest, ev):
    tok = _token_for(guest, user)
    r2 = guest.post("reset_password.php", {"token": tok, "password": "NewPassw0rd!", "password_confirm": "NewPassw0rd!"},
                    token_page=f"reset_password.php?token={tok}")
    ev.http("POST reset", r2)
    assert r2.status_code == 302 and "reset=ok" in r2.headers.get("Location", ""), strip_tags(r2.text)[:150]
    assert AnynClient().login(user.email, "NewPassw0rd!").status_code == 302, "mật khẩu mới không dùng được"
    assert AnynClient().login(user.email, user.password).status_code == 200, "mật khẩu cũ vẫn dùng được"


@tc("TC-PWD-04", "TS-03", "FR-03", "Token đặt lại mật khẩu không hợp lệ bị từ chối: đã dùng một lần, hết hạn, sai định dạng", "Có tài khoản và token hợp lệ",
    ["Dùng token T để reset rồi dùng lại T", "Tạo token mới, đặt expires_at về quá khứ rồi mở liên kết", "Mở reset_password.php với token 'abc', 'f'*64, \"' OR 1=1--\", rỗng"],
    "token đã dùng | expires_at = now-1 phút | abc | 'f'*64 | SQL | ''",
    "Mọi trường hợp báo 'invalid or has expired'; không hiện form đổi mật khẩu; không lỗi PHP/SQL; không đổi được mật khẩu bằng token đã dùng",
    "State Transition + Boundary Value Analysis (time) + Error Guessing", "Boundary", "High")
def test_pwd_04(user, guest, ev):
    tok = _token_for(guest, user)
    guest.post("reset_password.php", {"token": tok, "password": "NewPassw0rd!", "password_confirm": "NewPassw0rd!"}, token_page=f"reset_password.php?token={tok}")
    again = AnynClient().get(f"reset_password.php?token={tok}")
    ev.note(f"token dùng lại: {'bị từ chối' if 'invalid or has expired' in strip_tags(again.text) else 'DÙNG LẠI ĐƯỢC'}")
    assert "invalid or has expired" in strip_tags(again.text), "token dùng lại được"
    tok2 = _token_for(guest, user)
    db.run("UPDATE password_resets SET expires_at=datetime('now','-1 minutes') WHERE user_id=?", (user.user_id,))
    page = guest.get(f"reset_password.php?token={tok2}")
    ev.note(f"token hết hạn: {'bị từ chối' if 'invalid or has expired' in strip_tags(page.text) else 'CÒN DÙNG ĐƯỢC'}")
    assert "invalid or has expired" in strip_tags(page.text) and "password_confirm" not in page.text
    for t in ["abc", "f" * 64, "' OR 1=1--", ""]:
        r = guest.get("reset_password.php?token=" + t)
        assert r.status_code == 200 and "invalid or has expired" in strip_tags(r.text) and "SQLSTATE" not in r.text, t


@tc("TC-PWD-05", "TS-03", "FR-03", "Giới hạn số lần yêu cầu reset (5 / 15 phút)", "—",
    ["Gửi 5 yêu cầu cho cùng email", "Gửi yêu cầu thứ 6"], "email bất kỳ",
    "Yêu cầu 1–5 được chấp nhận; yêu cầu 6 báo 'Too many requests'", "Boundary Value Analysis", "Boundary", "Medium")
def test_pwd_05(guest, ev):
    mail = f"{uniq('rl')}@qa.test"
    for i in range(5):
        assert SENT in strip_tags(_forgot(guest, mail).text), f"request {i+1}"
    assert "Too many requests" in strip_tags(_forgot(guest, mail).text)


@tc("TC-PWD-06", "TS-03", "FR-03", "Liên kết reset KHÔNG được hiển thị cho người gửi yêu cầu (chống chiếm tài khoản)",
    "Cấu hình mặc định của mã nguồn (APP_ENV chưa đặt); máy chủ không gửi được email",
    ["Người lạ (chưa đăng nhập) nhập email của nạn nhân vào Forgot password", "Quan sát phản hồi"], "email nạn nhân (không phải của người gửi)",
    "Phản hồi chỉ có thông báo trung tính; KHÔNG chứa liên kết/token reset", "Error Guessing (security)", "Invalid", "High", bug=["BUG-001"])
def test_pwd_06(user, ev):
    attacker = AnynClient()
    r = _forgot(attacker, user.email)
    link, tok = _link(r)
    ev.note(f"reset link in response to an anonymous requester: {'YES -> ' + link[:70] if link else 'no'}")
    assert not link, "liên kết đặt lại mật khẩu bị lộ cho người gửi yêu cầu → chiếm tài khoản"


@tc("TC-PWD-07", "TS-03", "FR-03", "Đổi mật khẩu không hợp lệ: mật khẩu hiện tại sai, mật khẩu mới yếu / trùng mật khẩu cũ / xác nhận không khớp", "Đã đăng nhập",
    ["Profile → Change password với current sai", "Thử mật khẩu mới yếu, trùng mật khẩu cũ, xác nhận không khớp"],
    "current=Wrong#123 | new='abc' | new=current | confirm khác", "Mỗi trường hợp bị từ chối với thông báo phù hợp ('Current password is incorrect' cho trường hợp đầu); mật khẩu không đổi",
    "Equivalence Partitioning (invalid class) + Decision Table", "Invalid", "High")
def test_pwd_07(user, ev):
    r = user.post("profile.php", {"change_password": "1", "current_password": "Wrong#123", "new_password": "NewPassw0rd1", "new_password_confirm": "NewPassw0rd1"})
    t = strip_tags(r.text)
    ev.note(t[t.lower().find("current"):][:80])
    assert "incorrect" in t.lower() or "wrong" in t.lower() or "not correct" in t.lower(), t[:200]
    assert AnynClient().login(user.email, user.password).status_code == 302, "mật khẩu cũ bị thay đổi"
    for new, conf in [("abc", "abc"), (user.password, user.password), ("NewPassw0rd1", "Different1x")]:
        r = user.post("profile.php", {"change_password": "1", "current_password": user.password, "new_password": new, "new_password_confirm": conf})
        ok = AnynClient().login(user.email, user.password).status_code == 302
        ev.note(f"new={new[:12]!r} conf={conf[:12]!r}: mật khẩu cũ vẫn hợp lệ={ok}")
        assert ok, f"mật khẩu bị đổi với dữ liệu {new!r}"


@tc("TC-PWD-08", "TS-03", "FR-03", "Đổi mật khẩu hợp lệ", "Đã đăng nhập",
    ["Nhập current đúng, new hợp lệ, confirm khớp"], "new=NewPassw0rd1",
    "Thông báo thành công; đăng nhập được bằng mật khẩu mới, mật khẩu cũ bị từ chối; session ID được tái tạo",
    "Equivalence Partitioning (valid class)", "Valid", "High")
def test_pwd_08(user, ev):
    sid = user.s.cookies.get("PHPSESSID")
    r = user.post("profile.php", {"change_password": "1", "current_password": user.password, "new_password": "NewPassw0rd1", "new_password_confirm": "NewPassw0rd1"})
    t = strip_tags(r.text)
    assert "password" in t.lower() and ("changed" in t.lower() or "updated" in t.lower()), t[:200]
    assert AnynClient().login(user.email, "NewPassw0rd1").status_code == 302
    assert AnynClient().login(user.email, user.password).status_code == 200
    ev.note(f"session id changed: {sid != user.s.cookies.get('PHPSESSID')}")
