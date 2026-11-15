"""TS-02 — Login / logout / throttling (FR-02)."""
import re

import requests

from framework import db
from framework.client import AnynClient, strip_tags
from framework.config import ALICE, PAGES, SEED_PASSWORD
from framework.tcmeta import tc

GENERIC = "Invalid email or password"


def _txt(r):
    return strip_tags(r.text)


@tc("TC-LOG-01", "TS-02", "FR-02", "Đăng nhập thành công (email đúng chữ hoa/thường hoặc viết hoa toàn bộ)", "Tài khoản alice@anyn.test tồn tại",
    ["Mở trang Login", "Nhập email + password đúng", "Bấm Sign in", "Lặp lại với email viết HOA"], "alice@anyn.test / User@12345; ALICE@ANYN.TEST / User@12345",
    "Chuyển hướng 302 về trang chủ; thanh điều hướng hiện username; truy cập profile.php được; email không phân biệt hoa/thường",
    "Equivalence Partitioning (valid class)", "Valid", "High")
def test_log_01(guest, ev):
    r = guest.login(ALICE["email"], SEED_PASSWORD)
    ev.http("POST login", r)
    assert r.status_code == 302 and "index.php" in r.headers.get("Location", ""), f"không redirect về trang chủ: {r.status_code}"
    home = guest.get("index.php", allow_redirects=True)
    assert "alice_qa" in home.text, "navbar không hiển thị username"
    assert guest.get("profile.php").status_code == 200, "không vào được profile sau đăng nhập"
    other = AnynClient()
    r = other.login("ALICE@ANYN.TEST", SEED_PASSWORD)
    ev.http("POST login (email viết HOA)", r)
    assert r.status_code == 302, f"HTTP {r.status_code}: {_txt(r)[:100]}"


@tc("TC-LOG-02", "TS-02", "FR-02", "Đăng nhập không hợp lệ: sai mật khẩu hoặc để trống trường", "Tài khoản alice tồn tại",
    ["Nhập email đúng + mật khẩu sai", "Gửi POST login với email/password rỗng (bỏ qua kiểm tra HTML required)"], "alice@anyn.test / Wrong#9999; email='' / password=''",
    "Ở lại trang login (HTTP 200); thông báo chung 'Invalid email or password.'; không tạo session đăng nhập; không lỗi/Warning PHP",
    "Equivalence Partitioning (invalid classes: sai mật khẩu, rỗng)", "Invalid", "High")
def test_log_02(guest, ev):
    r = guest.login(ALICE["email"], "Wrong#9999")
    assert r.status_code == 200 and GENERIC in _txt(r)
    assert guest.get("profile.php").status_code == 302, "truy cập được trang cần đăng nhập"
    r = guest.login("", "")
    ev.http("POST login (rỗng)", r)
    assert r.status_code == 200 and GENERIC in _txt(r) and "Warning" not in r.text


@tc("TC-LOG-03", "TS-02", "FR-02", "Email không tồn tại — cùng thông báo lỗi (chống dò tài khoản)", "—",
    ["Đăng nhập với email chưa đăng ký"], "ghost@nowhere.test / Whatever1",
    "Thông báo GIỐNG HỆT trường hợp sai mật khẩu, không tiết lộ email có tồn tại", "Error Guessing", "Invalid", "High")
def test_log_03(guest, ev):
    a = _txt(guest.login("ghost@nowhere.test", "Whatever1"))
    b = _txt(AnynClient().login(ALICE["email"], "Wrong#9999"))
    ev.note(f"unknown-email msg == wrong-password msg: {a == b}")
    assert GENERIC in a and a == b, "thông báo khác nhau → lộ thông tin tồn tại tài khoản"


@tc("TC-LOG-04", "TS-02", "FR-02", "Khoá tạm thời sau 5 lần sai liên tiếp và bộ đếm được xoá khi đăng nhập đúng (state transition)", "Chưa có lần thử nào",
    ["Sai 3 lần, đăng nhập đúng, đăng xuất, sai thêm 4 lần rồi đăng nhập đúng", "Xoá bộ đếm; đăng nhập sai 5 lần liên tiếp", "Lần 6: dùng mật khẩu ĐÚNG"], "alice@anyn.test",
    "Bộ đếm về 0 sau đăng nhập đúng nên 4 lần sai tiếp theo chưa bị khoá; lần 1–5 báo 'Invalid email or password'; lần 6 (kể cả đúng mật khẩu) báo 'Too many failed attempts'",
    "State Transition Testing", "Boundary", "High")
def test_log_04(guest, ev):
    for i in range(3):
        guest.login(ALICE["email"], "bad!Pass1")
    assert guest.login(ALICE["email"], SEED_PASSWORD).status_code == 302
    guest.logout()
    for i in range(4):
        guest.login(ALICE["email"], "bad!Pass1")
    r = guest.login(ALICE["email"], SEED_PASSWORD)
    assert r.status_code == 302, f"bị khoá sớm (bộ đếm không được xoá): {_txt(r)[:80]}"
    guest.logout()
    db.clear_login_attempts()
    for i in range(1, 6):
        assert GENERIC in _txt(guest.login(ALICE["email"], f"bad{i}Pass!"))
    r = guest.login(ALICE["email"], SEED_PASSWORD)
    t = _txt(r)
    ev.note(f"attempt 6 (correct pw): HTTP {r.status_code} -> {t[t.find('Too'):][:60] if 'Too' in t else t[:80]}")
    assert "Too many" in t and r.status_code == 200, "không khoá sau 5 lần sai"


@tc("TC-LOG-05", "TS-02", "FR-02", "Đăng xuất huỷ phiên làm việc", "Đã đăng nhập",
    ["Ghi lại cookie PHPSESSID", "Bấm Logout", "Dùng lại cookie cũ truy cập profile.php"], "—",
    "Sau logout trang profile chuyển về login; cookie cũ không còn hiệu lực", "Use-case testing", "Valid", "High")
def test_log_05(alice, ev):
    sid = alice.s.cookies.get("PHPSESSID")
    r = alice.logout()
    ev.http("GET logout", r)
    replay = requests.get(PAGES + "/profile.php", cookies={"PHPSESSID": sid}, allow_redirects=False)
    ev.http("replay old session", replay)
    assert replay.status_code == 302 and "login" in replay.headers.get("Location", ""), "session cũ vẫn dùng được sau logout"


@tc("TC-LOG-06", "TS-02", "FR-02", "Session ID được tái tạo sau đăng nhập (chống session fixation)", "—",
    ["Mở trang login (nhận PHPSESSID)", "Đăng nhập", "So sánh PHPSESSID"], "—",
    "PHPSESSID sau đăng nhập khác PHPSESSID trước đăng nhập", "Error Guessing (security)", "Valid", "High")
def test_log_06(guest, ev):
    guest.get("login.php")
    before = guest.s.cookies.get("PHPSESSID")
    guest.login(ALICE["email"], SEED_PASSWORD)
    after = guest.s.cookies.get("PHPSESSID")
    ev.note(f"before={before[:8]}… after={after[:8]}…")
    assert before and after and before != after


@tc("TC-LOG-07", "TS-02", "FR-02", "Tiện ích đăng nhập: 'Remember email' và chuyển hướng khi đã đăng nhập (trang login/register)", "Tài khoản alice tồn tại",
    ["Đăng nhập với tick Remember, quan sát cookie, mở lại trang login", "Khi đã đăng nhập mở /pages/login.php", "Khi đã đăng nhập mở /pages/register.php"], "alice@anyn.test + remember=1",
    "Có cookie ghi nhớ email với cờ HttpOnly + SameSite=Lax; trang login điền sẵn email; login/register khi đã đăng nhập → HTTP 302 về trang chủ",
    "Decision Table + Use-case testing", "Valid", "Low")
def test_log_07(guest, alice, ev):
    r = guest.login(ALICE["email"], SEED_PASSWORD, remember=True)
    sc = r.headers.get("Set-Cookie", "")
    ev.note("Set-Cookie: " + re.sub(r"PHPSESSID=\w+", "PHPSESSID=…", sc)[:200])
    assert "remember" in sc.lower(), "không có cookie remember"
    assert "httponly" in sc.lower() and "samesite=lax" in sc.lower(), "cookie thiếu HttpOnly/SameSite"
    guest.logout()
    assert ALICE["email"] in guest.get("login.php", allow_redirects=True).text, "email không được điền sẵn"
    for page in ("login.php", "register.php"):
        r = alice.get(page)
        ev.http(f"GET {page} (đã đăng nhập)", r)
        assert r.status_code == 302, f"{page}: HTTP {r.status_code}"
        if page == "register.php":
            assert "index.php" in r.headers.get("Location", "")


@tc("TC-LOG-08", "TS-02", "FR-02", "SQL injection ở form đăng nhập", "—",
    ["Đăng nhập với email/password chứa SQL"], "email=\"' OR '1'='1' --\"; password=\"' OR '1'='1\"",
    "Đăng nhập thất bại với thông báo chung; không lỗi SQL; không có session đăng nhập", "Error Guessing (security)", "Invalid", "High")
def test_log_08(guest, ev):
    r = guest.login("' OR '1'='1' --", "' OR '1'='1")
    assert r.status_code == 200 and GENERIC in _txt(r) and "SQLSTATE" not in r.text
    assert guest.get("profile.php").status_code == 302


@tc("TC-LOG-09", "TS-02", "FR-02", "Kẻ tấn công không thể khoá tài khoản của người khác (lockout abuse)",
    "Nạn nhân alice có mật khẩu đúng", ["Kẻ tấn công (guest khác) gửi 5 lần đăng nhập sai với email của nạn nhân",
                                          "Nạn nhân đăng nhập với mật khẩu ĐÚNG từ trình duyệt riêng"], "email nạn nhân = alice@anyn.test",
    "Người dùng hợp lệ vẫn đăng nhập được (hệ thống nên giới hạn theo cặp email+IP hoặc dùng CAPTCHA/delay luỹ tiến)",
    "Error Guessing (abuse case)", "Invalid", "Medium", bug=["BUG-002"])
def test_log_09(ev):
    attacker = AnynClient()
    for i in range(5):
        attacker.login(ALICE["email"], f"atk{i}Pass!")
    # simulate a different client address for the victim: the app reads REMOTE_ADDR only, so a distinct IP is modelled in the DB
    db.run("UPDATE login_attempts SET ip='203.0.113.7'")      # the attacker's attempts came from another IP
    victim = AnynClient()
    r = victim.login(ALICE["email"], SEED_PASSWORD)
    t = _txt(r)
    ev.note(f"victim login with CORRECT password after attacker's 5 failures -> HTTP {r.status_code}: {t[t.find('Too'):][:70] if 'Too' in t else 'ok'}")
    assert r.status_code == 302, "nạn nhân bị khoá do hành vi của kẻ tấn công (DoS tài khoản)"
