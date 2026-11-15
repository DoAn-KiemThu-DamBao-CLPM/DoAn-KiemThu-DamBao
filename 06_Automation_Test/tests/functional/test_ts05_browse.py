"""TS-05 — Browse, search, filter, sort, paginate characters (FR-05)."""
import json
import re

from framework import db
from framework.client import AnynClient, strip_tags
from framework.tcmeta import tc

CARD = re.compile(r"window\.location\.href='pages/bot_detail\.php\?id=(\d+)'")


def ids(c, qs=""):
    r = c.get("index.php" + qs, allow_redirects=True)
    return [int(x) for x in CARD.findall(r.text)], r


def requests_quote(s):
    from urllib.parse import quote
    return quote(s, safe="")


@tc("TC-BRW-01", "TS-05", "FR-05", "Phân trang trang chủ: 24 nhân vật/trang và giá trị page ngoài biên (0, -1, abc, 3, 999)", "Có 40 nhân vật seed (= 2 trang)",
    ["Mở trang chủ và ?page=2", "Mở ?page=0, -1, abc, 3, 999"], "page=1,2 | 0 | -1 | abc | 3 | 999",
    "Trang 1 có 24 thẻ, trang 2 có 16 thẻ, không trùng nhau; page<1 hoặc không phải số → trang 1; page > tổng → trang cuối (16 thẻ); không lỗi",
    "Boundary Value Analysis", "Boundary", "High")
def test_brw_01(guest, ev):
    p1, _ = ids(guest)
    p2, _ = ids(guest, "?page=2")
    ev.note(f"page1={len(p1)} cards, page2={len(p2)} cards, overlap={len(set(p1) & set(p2))}")
    assert len(p1) == 24 and len(p2) == 16 and not set(p1) & set(p2)
    for q, exp in [("0", p1), ("-1", p1), ("abc", p1), ("3", p2), ("999", p2)]:
        got, r = ids(guest, "?page=" + q)
        ev.note(f"page={q}: HTTP {r.status_code}, {len(got)} thẻ")
        assert r.status_code == 200 and got == exp, f"page={q}"


@tc("TC-BRW-02", "TS-05", "FR-05", "Tìm kiếm theo tên: khớp một phần không phân biệt hoa/thường, không có kết quả, ký tự % và _ coi như ký tự thường", "—",
    ["Tìm '#007' và 'NIGHTBLADE'", "Tìm 'zzzzqqq'", "Tìm '%' và '_'"], "#007 | NIGHTBLADE | zzzzqqq | % | _",
    "'#007' trả đúng id=7; 'NIGHTBLADE' trả mọi nhân vật chứa 'Nightblade'; 'zzzzqqq' hiển thị 'No characters found'; '%' và '_' không khớp bản ghi nào",
    "Equivalence Partitioning (valid/invalid) + Error Guessing", "Valid", "High")
def test_brw_02(guest, ev):
    got, _ = ids(guest, "?search=%23007")
    assert got == [7], got
    got, _ = ids(guest, "?search=NIGHTBLADE")
    expect = {r["id"] for r in db.q("SELECT id FROM bots WHERE name LIKE '%nightblade%' OR description LIKE '%nightblade%'")}
    ev.note(f"NIGHTBLADE → {len(got)} kết quả (DB kỳ vọng {len(expect)}; trang 1 tối đa 24)")
    assert set(got) <= expect and len(got) == min(24, len(expect))
    got, r = ids(guest, "?search=zzzzqqq")
    assert got == [] and "No characters found" in r.text
    for q in ("%25", "_"):
        got, r = ids(guest, "?search=" + q)
        ev.note(f"search={q}: {len(got)} kết quả")
        assert got == [], f"wildcard {q} khớp {len(got)} bản ghi"


@tc("TC-BRW-03", "TS-05", "FR-05", "Dữ liệu độc hại ở ô tìm kiếm: SQL injection và XSS phản xạ", "—",
    ["Tìm \"' OR 1=1 --\", \"%' UNION SELECT 1,2,3--\", \"\\\\\"", "Tìm '\"><script>alert(1)</script>'"], "payload SQL; payload XSS",
    "Không lỗi SQL/HTTP 500, không lộ dữ liệu, kết quả rỗng; không có thẻ <script> thô trong HTML (giá trị được escape)", "Error Guessing (security)", "Invalid", "High")
def test_brw_03(guest, ev):
    for q in ["' OR 1=1 --", "%' UNION SELECT 1,2,3--", "\\", "\\'"]:
        got, r = ids(guest, "?search=" + requests_quote(q))
        ev.note(f"{q!r}: HTTP {r.status_code}, {len(got)} kết quả")
        assert r.status_code == 200 and "SQLSTATE" not in r.text and "Fatal" not in r.text and got == []
    payload = '"><script>alert(1)</script>'
    r = guest.get("index.php?search=" + requests_quote(payload) + "&theme=" + requests_quote(payload))
    assert "<script>alert(1)</script>" not in r.text, "XSS phản xạ"


@tc("TC-BRW-04", "TS-05", "FR-05", "Lọc theo chủ đề (theme)", "Seed có chủ đề Fantasy",
    ["Mở ?theme=Fantasy"], "theme=Fantasy", "Chỉ các nhân vật có chủ đề Fantasy; số lượng khớp DB", "Equivalence Partitioning", "Valid", "High")
def test_brw_04(guest, ev):
    exp = {r["bot_id"] for r in db.q("SELECT bot_id FROM bot_themes bt JOIN themes t ON t.id=bt.theme_id WHERE t.name='Fantasy'")}
    got, _ = ids(guest, "?theme=Fantasy")
    allexp = len(exp)
    ev.note(f"DB có {allexp} nhân vật Fantasy; trang 1 trả {len(got)}")
    assert set(got) <= exp and len(got) == min(24, allexp)


@tc("TC-BRW-05", "TS-05", "FR-05", "Kết hợp tìm kiếm + lọc chủ đề + sắp xếp", "—",
    ["?search=the&theme=Romance&sort=name"], "search=the; theme=Romance; sort=name",
    "Kết quả thoả đồng thời cả hai điều kiện và sắp xếp A→Z", "Pairwise / combination", "Valid", "Medium")
def test_brw_05(guest, ev):
    got, _ = ids(guest, "?search=the&theme=Romance&sort=name")
    rows = db.q("SELECT b.id, b.name FROM bots b WHERE (b.name LIKE '%the%' OR b.description LIKE '%the%') AND b.id IN "
                "(SELECT bot_id FROM bot_themes bt JOIN themes t ON t.id=bt.theme_id WHERE t.name='Romance') ORDER BY b.name ASC LIMIT 24")
    ev.note(f"kỳ vọng {[r['id'] for r in rows]}, thực tế {got}")
    assert got == [r["id"] for r in rows]


@tc("TC-BRW-06", "TS-05", "FR-05", "Chủ đề bị chặn (NSFW…): tham số theme bị bỏ qua; chủ đề không hiển thị và bị xoá khỏi DB ở phiên mới", "Chèn trực tiếp theme 'NSFW' gắn vào bot 1",
    ["Mở ?theme=NSFW, N.T.R, r-18", "Mở trang chủ & chi tiết bot 1 bằng phiên mới"], "NSFW | N.T.R | r-18",
    "Bộ lọc bị bỏ qua → trả danh sách chưa lọc (24 thẻ); không thấy 'NSFW' ở bộ lọc/thẻ; bản ghi theme bị purge khỏi DB", "Equivalence Partitioning (invalid class) + State Transition", "Invalid", "Medium")
def test_brw_06(guest, ev):
    base, _ = ids(guest)
    for t in ("NSFW", "N.T.R", "r-18"):
        got, _ = ids(guest, "?theme=" + requests_quote(t))
        assert got == base, f"theme={t} được áp dụng"
    tid = db.run("INSERT INTO themes (name) VALUES ('NSFW')")
    db.run("INSERT INTO bot_themes (bot_id, theme_id) VALUES (1, ?)", (tid,))
    c = AnynClient()
    home = c.get("index.php", allow_redirects=True).text
    detail = c.get("bot_detail.php?id=1", allow_redirects=True).text
    assert "NSFW" not in home and "NSFW" not in detail, "chủ đề bị chặn vẫn hiển thị"
    left = db.scalar("SELECT COUNT(*) FROM themes WHERE name='NSFW'")
    ev.note(f"themes còn lại tên NSFW sau phiên mới: {left}")
    assert left == 0, "chưa purge"


@tc("TC-BRW-07", "TS-05", "FR-05", "Sắp xếp: Newest / Top rated / A→Z / giá trị không hợp lệ; nhân vật ghim luôn đứng đầu ở Newest", "Seed ghim id 7, 21, 33",
    ["Mở trang chủ mặc định", "Mở ?sort=rating, ?sort=name, ?sort=hack"], "rating | name | hack",
    "Ba thẻ đầu ở chế độ Newest là các nhân vật ghim; rating: total_rating giảm dần; name: A→Z; 'hack' quay về mặc định Newest", "Decision Table + Experience-based", "Valid", "Medium")
def test_brw_07(guest, ev):
    default, _ = ids(guest)
    pinned = {r["id"] for r in db.q("SELECT id FROM bots WHERE is_pinned=1")}
    assert set(default[:len(pinned)]) == pinned, f"đầu trang: {default[:5]}"
    got, _ = ids(guest, "?sort=rating")
    exp = [r["id"] for r in db.q("SELECT id FROM bots ORDER BY total_rating DESC, created_at DESC LIMIT 24")]
    assert got == exp, "sort=rating sai"
    got, _ = ids(guest, "?sort=name")
    exp = [r["id"] for r in db.q("SELECT id FROM bots ORDER BY name ASC LIMIT 24")]
    assert got == exp, "sort=name sai"
    got, _ = ids(guest, "?sort=hack")
    assert got == default, "sort không hợp lệ không quay về mặc định"


@tc("TC-BRW-08", "TS-05", "FR-05", "API gợi ý tìm kiếm (search_suggestions.php)", "—",
    ["q='aria'", "q rỗng", "q 100 ký tự", "q='%'"], "aria | '' | 'a'*100 | %",
    "Trả JSON ≤ 5 phần tử; q rỗng → []; q dài được cắt 60 ký tự và không lỗi; '%' → []; Content-Type JSON",
    "Boundary Value Analysis", "Boundary", "Medium")
def test_brw_08(guest, ev):
    r = guest.get("search_suggestions.php?q=aria")
    data = json.loads(r.text)
    assert "application/json" in r.headers["Content-Type"] and 1 <= len(data) <= 5 and all("name" in d for d in data)
    assert json.loads(guest.get("search_suggestions.php?q=").text) == []
    assert guest.get("search_suggestions.php?q=" + "a" * 100).status_code == 200
    assert json.loads(guest.get("search_suggestions.php?q=%25").text) == []
    ev.note(f"q=aria → {len(data)} gợi ý")


@tc("TC-BRW-09", "TS-05", "FR-05", "Trang Collection: id hợp lệ / không tồn tại / thiếu id", "Seed có collection 1 (4 nhân vật)",
    ["Mở group_detail.php?id=1", "?id=9999", "(không có id)"], "1 | 9999 | —",
    "id=1 liệt kê đúng 4 nhân vật; id=9999 báo 'Collection does not exist!'; thiếu id báo 'Collection not found!'", "Equivalence Partitioning", "Valid", "Medium")
def test_brw_09(guest, ev):
    r = guest.get("group_detail.php?id=1")
    assert sorted(set(int(x) for x in re.findall(r"bot_detail\.php\?id=(\d+)", r.text))) == [1, 2, 3, 4]
    assert "Collection does not exist" in guest.get("group_detail.php?id=9999").text
    assert "Collection not found" in guest.get("group_detail.php").text


@tc("TC-BRW-10", "TS-05", "FR-05", "Trang chi tiết nhân vật không tồn tại trả HTTP 404", "—",
    ["Mở bot_detail.php?id=99999", "?id=abc"], "99999 | abc", "Thông báo không tìm thấy VÀ mã trạng thái HTTP 404 (như user.php)",
    "Equivalence Partitioning (invalid class)", "Invalid", "Low", bug=["BUG-003"])
def test_brw_10(guest, ev):
    for bad in ("99999", "abc"):
        r = guest.get("bot_detail.php?id=" + bad)
        ev.note(f"id={bad}: HTTP {r.status_code}, body has 'not found'={'not found' in r.text.lower()}")
        assert "not found" in r.text.lower()
        assert r.status_code == 404, f"id={bad}: HTTP {r.status_code} (soft-404, trang báo không tìm thấy nhưng trả 200)"
