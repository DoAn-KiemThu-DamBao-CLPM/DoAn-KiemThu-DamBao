"""TS-08 — Custom commission ordering (cash amount or gem voucher) (FR-08)."""
from framework import db, images
from framework.tcmeta import tc

BASE = dict(title="Fire knight", appearance="Red armour, scar over left eye", context="Exiled captain of the guard")


def order(c, files=None, **over):
    d = dict(BASE, submit_commission="1")
    d.update(over)
    return c.post("commission.php", d, files=files)


def rows(uid):
    return db.q("SELECT * FROM commissions WHERE user_id=? ORDER BY id DESC", (uid,))


def give_voucher(uid, kind="publish", n=1):
    for _ in range(n):
        db.run("INSERT INTO user_inventory (user_id,item_key,item_type,meta_json) VALUES (?,?,?,'{}')",
               (uid, f"coupon_commission_{kind}", f"commission_{kind}"))


def unused(uid, kind="publish"):
    return db.scalar("SELECT COUNT(*) FROM user_inventory WHERE user_id=? AND item_type=? AND used_at IS NULL",
                     (uid, f"commission_{kind}"))


@tc("TC-COM-01", "TS-08", "FR-08", "Đặt commission trả tiền hợp lệ (5 USD, cho phép công khai) → sang bước thanh toán",
    "Đã đăng nhập (0 gems)", ["Mở commission.php", "Nhập Title/Appearance/Context", "Nhập amount=5, tick allow_public", "Gửi"],
    "amount=5; allow_public=1", "Bước 2 hiển thị email PayPal + mã ORDER-<id>; 1 bản ghi commissions (Pending, amount_paid=5, is_private=0); +25 gems",
    "Use-case testing + Equivalence Partitioning", "Valid", "High")
def test_com_01(user, ev):
    r = order(user, amount="5", allow_public="1")
    row = rows(user.user_id)
    ev.note(f"commissions={len(row)}, row={ {k: row[0][k] for k in ('status', 'amount_paid', 'is_private')} if row else None}, gems={db.gems(user.user_id)}")
    assert r.status_code == 200 and "prismvow.art@gmail.com" in r.text and f"ORDER-{row[0]['id']}" in r.text
    assert len(row) == 1 and row[0]["status"] == "Pending" and float(row[0]["amount_paid"]) == 5.0 and row[0]["is_private"] == 0
    assert db.gems(user.user_id) == 25


@tc("TC-COM-02", "TS-08", "FR-08", "Quy tắc riêng tư theo số tiền và giới hạn 1000 USD (4.99 / 5 / 1000 / 5000)",
    "Đã đăng nhập", ["Gửi đơn với từng cặp (amount, allow_public)"],
    "(4.99,✓) (5,✓) (5,✗) (1000,✓) (5000,✓)", "Dưới 5 USD luôn private dù tick public; từ 5 USD + tick → public; không tick → private; amount > 1000 bị chặn về 1000",
    "Boundary Value Analysis + Decision Table", "Boundary", "High")
def test_com_02(user, ev):
    cases = [("4.99", True, 4.99, 1), ("5", True, 5.0, 0), ("5", False, 5.0, 1), ("1000", True, 1000.0, 0), ("5000", True, 1000.0, 0)]
    for amt, pub, exp_amt, exp_priv in cases:
        d = {"amount": amt}
        if pub:
            d["allow_public"] = "1"
        order(user, **d)
        row = rows(user.user_id)[0]
        ev.note(f"amount={amt} public={pub} → lưu amount={float(row['amount_paid'])}, is_private={row['is_private']} (mong đợi {exp_amt}/{exp_priv})")
        assert float(row["amount_paid"]) == exp_amt and row["is_private"] == exp_priv


@tc("TC-COM-03", "TS-08", "FR-08", "Kiểm tra dữ liệu: thiếu trường bắt buộc, liên kết tham chiếu sai, tệp đội lốt ảnh",
    "Đã đăng nhập", ["Gửi thiếu Title / Appearance / Context", "Gửi image_url=javascript:alert(1)", "Tải file PHP đổi tên .png"],
    "title='' | appearance='' | context='' | javascript: | shell.png (PHP)",
    "Hiển thị thông báo lỗi tương ứng; không có bản ghi commissions; không thưởng gems",
    "Decision Table + Error Guessing", "Invalid", "High")
def test_com_03(user, ev):
    for over in (dict(title=""), dict(appearance=""), dict(context="   ")):
        r = order(user, amount="5", **over)
        assert "Please fill in all required fields" in r.text
    r = order(user, amount="5", image_url="javascript:alert(1)")
    assert "Reference link must be a valid http(s) URL" in r.text
    r = order(user, amount="5", files={"com_image_file": ("shell.png", images.PHP_SCRIPT, "image/png")})
    assert "Invalid image format" in r.text
    ev.note(f"commissions={len(rows(user.user_id))}, gems={db.gems(user.user_id)}")
    assert rows(user.user_id) == [] and db.gems(user.user_id) == 0


@tc("TC-COM-04", "TS-08", "FR-08", "Đơn 0 USD không được tạo ra phần thưởng gems (chống farm gems)",
    "Đã đăng nhập (0 gems)", ["Gửi đơn commission với amount=0 (hoặc bỏ trống) và không dùng voucher", "Lặp lại lần 2"],
    "amount=0 | amount rỗng", "Đơn không có giá trị hoặc bị từ chối; nếu vẫn tạo đơn thì KHÔNG được cộng 25 gems / mission 'submit_commission'",
    "Error Guessing (business-logic abuse)", "Invalid", "High", bug=["BUG-006"])
def test_com_04(user, ev):
    order(user, amount="0")
    order(user, amount="")
    n = len(rows(user.user_id))
    g = db.gems(user.user_id)
    ev.note(f"2 đơn 0 USD → {n} bản ghi commissions, gems={g}")
    assert g == 0, f"2 đơn 0 USD đã tạo {n} bản ghi và cộng {g} gems (đổi được voucher commission trị giá ≥ 5 USD sau vài ngày)"


@tc("TC-COM-05", "TS-08", "FR-08", "Đặt commission bằng voucher: Published / Unlisted / không có voucher",
    "Tài khoản có 1 voucher publish + 1 voucher unlisted", ["Dùng voucher publish", "Dùng voucher unlisted", "Dùng voucher publish khi đã hết"],
    "use_voucher=publish | unlisted | publish", "Voucher bị tiêu thụ (used_at); đơn amount=5, is_private=0 (publish) / 1 (unlisted), admin_note 'Gem voucher: …', bỏ qua bước thanh toán; hết voucher → lỗi, không tạo đơn",
    "State Transition (voucher: unused→used) + Equivalence Partitioning", "Valid", "High")
def test_com_05(user, ev):
    give_voucher(user.user_id, "publish")
    give_voucher(user.user_id, "unlisted")
    r = order(user, use_voucher="publish")
    a = rows(user.user_id)[0]
    ev.note(f"publish: amount={a['amount_paid']} private={a['is_private']} note={a['admin_note']!r}; voucher còn lại={unused(user.user_id)}")
    assert float(a["amount_paid"]) == 5 and a["is_private"] == 0 and a["admin_note"] == "Gem voucher: Published"
    assert "prismvow.art@gmail.com" not in r.text and unused(user.user_id, "publish") == 0
    order(user, use_voucher="unlisted")
    b = rows(user.user_id)[0]
    assert b["is_private"] == 1 and b["admin_note"] == "Gem voucher: Unlisted" and unused(user.user_id, "unlisted") == 0
    n = len(rows(user.user_id))
    r = order(user, use_voucher="publish")
    assert "No Published commission voucher available" in r.text and len(rows(user.user_id)) == n


@tc("TC-COM-06", "TS-08", "FR-08", "Voucher không được mất khi đơn bị từ chối vì ảnh/liên kết sai",
    "Tài khoản có 2 voucher publish", ["Dùng voucher kèm image_url=javascript:alert(1)", "Dùng voucher kèm file PHP đội lốt ảnh"],
    "use_voucher=publish + dữ liệu ảnh sai", "Đơn bị từ chối (không có bản ghi) và cả 2 voucher vẫn chưa dùng (used_at = NULL)",
    "Error Guessing (side effect on failure)", "Invalid", "High", bug=["BUG-007"])
def test_com_06(user, ev):
    give_voucher(user.user_id, "publish", 2)
    r1 = order(user, use_voucher="publish", image_url="javascript:alert(1)")
    r2 = order(user, use_voucher="publish", files={"com_image_file": ("shell.png", images.PHP_SCRIPT, "image/png")})
    left = unused(user.user_id, "publish")
    ev.note(f"2 lần gửi thất bại ({'URL sai' if 'valid http(s)' in r1.text else '?'}, {'ảnh sai' if 'Invalid image' in r2.text else '?'}) → voucher chưa dùng còn {left}/2; đơn tạo ra={len(rows(user.user_id))}")
    assert rows(user.user_id) == []
    assert left == 2, f"voucher bị tiêu thụ trước khi kiểm tra ảnh: còn {left}/2 (người dùng mất voucher trị giá 200 gems)"
