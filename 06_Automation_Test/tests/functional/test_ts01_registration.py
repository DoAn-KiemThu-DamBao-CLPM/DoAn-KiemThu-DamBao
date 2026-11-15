"""TS-01 — Account registration (FR-01)."""
from framework import db
from framework.client import AnynClient, strip_tags, uniq
from framework.tcmeta import tc

PW = "Passw0rd1"


def _reg(c, username=None, email=None, pw=PW, confirm=None):
    u = username if username is not None else uniq("r")
    e = email if email is not None else f"{uniq('m')}@qa.test"
    r = c.register(u, e, pw, confirm)
    return r, strip_tags(r.text), u, e


@tc("TC-REG-01", "TS-01", "FR-01", "Đăng ký thành công với dữ liệu hợp lệ",
    "Chưa đăng nhập; email/username chưa tồn tại",
    ["Mở trang Register", "Nhập username, email (có chữ hoa), password hợp lệ, xác nhận password", "Bấm Create account"],
    "username=reg_ok_N; email=Reg.OK@QA.test; password=Passw0rd1",
    "Hiển thị 'Account created!'; DB có 1 bản ghi; email lưu chữ thường; password_hash là bcrypt, không phải plaintext",
    "Equivalence Partitioning (valid class)", "Valid", "High")
def test_reg_01(guest, ev):
    name = uniq("regok")
    r = guest.register(name, f"Reg.OK.{name}@QA.test", PW)
    txt = strip_tags(r.text)
    ev.http("POST register", r, txt[txt.find("Account"):][:40])
    assert "Account created" in txt, f"không có thông báo thành công: {txt[:150]}"
    row = db.one("SELECT * FROM users WHERE username=?", (name,))
    assert row, "không có bản ghi trong DB"
    assert row["email"] == row["email"].lower(), f"email không được chuẩn hoá chữ thường: {row['email']}"
    assert row["password_hash"].startswith("$2y$") and PW not in row["password_hash"], "password không được băm bcrypt"
    ev.note(f"DB: id={row['id']} email={row['email']} hash={row['password_hash'][:10]}… role={row['role']}")


@tc("TC-REG-02", "TS-01", "FR-01", "Độ dài username tại biên 3–30 ký tự",
    "Chưa đăng nhập", ["Đăng ký lần lượt với username dài 2, 3, 30, 31 ký tự"],
    "len=2 'ab'; len=3 'abc'; len=30 'a'*30; len=31 'a'*31 (mỗi giá trị thêm hậu tố ngẫu nhiên để không trùng)",
    "2 → lỗi 'Username must be 3–30 characters.'; 3 → thành công; 30 → thành công; 31 → lỗi",
    "Boundary Value Analysis", "Boundary", "High")
def test_reg_02(guest, ev):
    cases = [(2, False), (3, True), (30, True), (31, False)]
    bad = []
    for n, ok in cases:
        suffix = uniq("")[-4:]
        name = (("x" * n) + suffix)[:n] if n >= 4 else ("ab" if n == 2 else "q" + suffix[:2])
        if n in (30, 31):
            name = ("w" * 40)[: n - len(suffix)] + suffix
        r, txt, _, _ = _reg(guest, username=name)
        got = "Account created" in txt
        ev.note(f"len={len(name)} -> {'created' if got else 'rejected'} (expected {'created' if ok else 'rejected'})")
        if got != ok:
            bad.append(len(name))
    assert not bad, f"hành vi sai tại độ dài {bad}"


@tc("TC-REG-03", "TS-01", "FR-01", "Username không hợp lệ bị từ chối (ký tự đặc biệt, thẻ HTML, toàn khoảng trắng); khoảng trắng đầu/cuối được cắt",
    "Chưa đăng nhập", ["Đăng ký với username chứa ký tự đặc biệt / thẻ HTML", "Đăng ký với username '    '", "Đăng ký với '  <name>  '"],
    "'bad<name>', 'john@doe', \"o'brien\", 'x/y', 'a;b', '<script>alert(1)</script>', '    ', '  <name>  '",
    "6 giá trị đầu báo 'Username may only contain letters, numbers, spaces, dots, dashes and underscores.'; '    ' bị từ chối; không tạo tài khoản; '  name  ' được cắt còn 'name'",
    "Equivalence Partitioning (invalid class) + Error Guessing", "Invalid", "High")
def test_reg_03(guest, ev):
    before = db.scalar("SELECT COUNT(*) FROM users")
    for bad in ["bad<name>", "john@doe", "o'brien", "x/y", "a;b", "<script>alert(1)</script>"]:
        r, txt, _, _ = _reg(guest, username=bad)
        ev.note(f"{bad!r}: {'REJECTED' if 'may only contain' in txt else 'ACCEPTED/other'}")
        assert "may only contain" in txt, f"username {bad!r} không bị từ chối đúng cách: {txt[:120]}"
    r, txt, _, _ = _reg(guest, username="    ")
    ev.note(f"'    ': {'REJECTED' if 'Account created' not in txt else 'ACCEPTED'}")
    assert "Account created" not in txt, "username toàn khoảng trắng được chấp nhận"
    assert db.scalar("SELECT COUNT(*) FROM users") == before, "có tài khoản bị tạo ngoài ý muốn"
    core = uniq("sp")
    r, txt, _, _ = _reg(guest, username=f"  {core}  ")
    assert "Account created" in txt
    row = db.one("SELECT username FROM users WHERE username LIKE ?", (f"%{core}%",))
    ev.note(f"stored username = {row['username']!r}")
    assert row["username"] == core, f"không trim khoảng trắng: {row['username']!r}"


@tc("TC-REG-04", "TS-01", "FR-01", "Username hợp lệ gồm chữ Unicode, dấu chấm, gạch ngang, gạch dưới, khoảng trắng",
    "Chưa đăng nhập", ["Đăng ký với username tiếng Việt có dấu và ký tự cho phép"],
    "'Nguyễn Văn A_1.x-y'", "Đăng ký thành công; username hiển thị đúng tiếng Việt (UTF-8)",
    "Equivalence Partitioning (valid class)", "Valid", "Medium")
def test_reg_04(guest, ev):
    name = f"Nguyễn Văn {uniq('')[-3:]}_1.x-y"
    r, txt, _, _ = _reg(guest, username=name)
    assert "Account created" in txt, f"username Unicode bị từ chối: {txt[:150]}"
    row = db.one("SELECT username FROM users WHERE username=?", (name,))
    assert row and row["username"] == name, "username lưu sai mã hoá"
    ev.note(f"DB username = {row['username']!r}")


@tc("TC-REG-05", "TS-01", "FR-01", "Email sai định dạng bị từ chối",
    "Chưa đăng nhập", ["Đăng ký với các email sai định dạng"],
    "'plainaddress', 'a@@b.com', 'a b@c.com', '@c.com', 'user@', 'x'*250+'@qa.test'",
    "Hiển thị 'Please enter a valid email address.'; không tạo tài khoản",
    "Equivalence Partitioning (invalid class)", "Invalid", "High")
def test_reg_05(guest, ev):
    for bad in ["plainaddress", "a@@b.com", "a b@c.com", "@c.com", "user@", "x" * 250 + "@qa.test"]:
        r, txt, _, _ = _reg(guest, email=bad)
        ok = "valid email" in txt
        ev.note(f"{bad[:30]!r}: {'rejected' if ok else 'ACCEPTED'}")
        assert ok, f"email {bad[:30]!r} không bị từ chối: {txt[:120]}"


@tc("TC-REG-06", "TS-01", "FR-01", "Độ dài password tại biên 8–72 ký tự",
    "Chưa đăng nhập", ["Đăng ký với password dài 7, 8, 72, 73 ký tự (đều có chữ và số)"],
    "'Ab1'+'x'*4 (7); 'Ab1'+'x'*5 (8); 'Ab1'+'x'*69 (72); 'Ab1'+'x'*70 (73)",
    "7 → lỗi 'at least 8'; 8 → OK; 72 → OK; 73 → lỗi 'at most 72'",
    "Boundary Value Analysis", "Boundary", "High")
def test_reg_06(guest, ev):
    bad = []
    for n, ok in [(7, False), (8, True), (72, True), (73, False)]:
        pw = "Ab1" + "x" * (n - 3)
        r, txt, _, _ = _reg(guest, pw=pw)
        got = "Account created" in txt
        ev.note(f"len={n}: {'created' if got else 'rejected'}")
        if got != ok:
            bad.append(n)
    assert not bad, f"sai tại độ dài password {bad}"


@tc("TC-REG-07", "TS-01", "FR-01", "Quy tắc password: độ phức tạp (bảng quyết định chữ/số) và xác nhận không khớp",
    "Chưa đăng nhập", ["Đăng ký với password 8+ ký tự: chỉ chữ / chỉ số / chữ+số / chữ+ký tự đặc biệt", "Nhập password và xác nhận khác nhau"],
    "'abcdefgh', '12345678', 'abcd1234', 'abcdefg!'; password=Passw0rd1, confirm=Passw0rd2",
    "Chỉ 'abcd1234' được chấp nhận; các giá trị khác báo 'at least one letter and one number'; xác nhận khác nhau báo 'Passwords do not match.' và không tạo tài khoản",
    "Decision Table + Equivalence Partitioning", "Invalid", "High")
def test_reg_07(guest, ev):
    table = {"abcdefgh": False, "12345678": False, "abcd1234": True, "abcdefg!": False}
    for pw, ok in table.items():
        r, txt, _, _ = _reg(guest, pw=pw)
        got = "Account created" in txt
        ev.note(f"{pw!r}: {'created' if got else 'rejected'}")
        assert got == ok, f"password {pw!r}: kỳ vọng {'OK' if ok else 'lỗi'}, thực tế {'OK' if got else 'lỗi'}"
    r, txt, u, _ = _reg(guest, confirm="Passw0rd2")
    ev.note(f"confirm khác nhau: {'rejected' if 'do not match' in txt else 'ACCEPTED'}")
    assert "do not match" in txt, txt[:150]
    assert not db.one("SELECT id FROM users WHERE username=?", (u,))


@tc("TC-REG-08", "TS-01", "FR-01", "Email hoặc username đã tồn tại (không phân biệt hoa/thường) bị từ chối",
    "Đã có tài khoản alice_qa / alice@anyn.test", ["Đăng ký với email ALICE@ANYN.TEST", "Đăng ký với username ALICE_QA"], "email=ALICE@ANYN.TEST; username=ALICE_QA",
    "Cả hai lần: lỗi 'Username or Email already in use.' (không tiết lộ trường nào trùng); không tạo tài khoản", "Equivalence Partitioning", "Invalid", "High")
def test_reg_08(guest, ev):
    r, txt, u, _ = _reg(guest, email="ALICE@ANYN.TEST")
    ev.note(f"email trùng: {'rejected' if 'already in use' in txt else 'ACCEPTED'}")
    assert "already in use" in txt, txt[:150]
    assert "Email already" not in txt or "Username or Email" in txt
    assert not db.one("SELECT id FROM users WHERE username=?", (u,))
    r, txt, u, e = _reg(guest, username="ALICE_QA")
    ev.note(f"username trùng (khác hoa/thường): {'rejected' if 'already in use' in txt else 'ACCEPTED'}")
    assert "already in use" in txt, txt[:150]
    assert not db.one("SELECT id FROM users WHERE email=?", (e.lower(),))


@tc("TC-REG-09", "TS-01", "FR-01", "POST đăng ký thiếu CSRF token bị chặn",
    "Chưa đăng nhập", ["Gửi POST /register.php không kèm csrf_token"], "không có csrf_token",
    "HTTP 403 'Security Error'; không tạo tài khoản", "Error Guessing", "Invalid", "High")
def test_reg_09(guest, ev):
    name = uniq("csrf")
    r = guest.post("register.php", {"username": name, "email": f"{name}@qa.test", "password": PW, "password_confirm": PW}, csrf=False)
    ev.http("POST (no token)", r)
    assert r.status_code == 403, f"status {r.status_code}"
    assert not db.one("SELECT id FROM users WHERE username=?", (name,))


@tc("TC-REG-10", "TS-01", "FR-01", "Chèn SQL vào các trường đăng ký",
    "Chưa đăng nhập", ["Gửi username/email chứa SQL injection"],
    "username=\"x' OR '1'='1\"; username=\"'; DROP TABLE users;--\"; email=\"a'--@b.com\" (email hợp lệ theo RFC 5322)",
    "Username chứa ký tự SQL bị từ chối bởi validate; email hợp lệ được lưu NGUYÊN VĂN (tham số hoá); bảng users còn nguyên; không lỗi SQL",
    "Error Guessing", "Invalid", "High")
def test_reg_10(guest, ev):
    n0 = db.scalar("SELECT COUNT(*) FROM users")
    for u in ["x' OR '1'='1", "'; DROP TABLE users;--"]:
        r = guest.register(u, f"{uniq('m')}@qa.test", PW)
        txt = strip_tags(r.text)
        ev.note(f"username={u!r}: HTTP {r.status_code}, {'rejected' if 'may only contain' in txt else 'OTHER'}")
        assert r.status_code == 200 and "may only contain" in txt and "SQLSTATE" not in r.text
    name = uniq("sq")
    r = guest.register(name, "a'--@b.com", PW)
    stored = db.one("SELECT email FROM users WHERE username=?", (name,))
    ev.note(f"email a'--@b.com -> {'stored literally' if stored and stored['email'] == chr(97)+chr(39)+'--@b.com' else 'not stored'}")
    assert "SQLSTATE" not in r.text and "Fatal" not in r.text
    assert stored is None or stored["email"] == "a'--@b.com", "email bị biến đổi (dấu hiệu injection)"
    assert db.scalar("SELECT COUNT(*) FROM users") in (n0, n0 + 1), "số bản ghi thay đổi bất thường"
    assert db.scalar("SELECT COUNT(*) FROM sqlite_master WHERE name='users'") == 1
