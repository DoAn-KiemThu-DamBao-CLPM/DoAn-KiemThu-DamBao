"""Non-functional: performance / load tests (indicative — see Test Plan 'Threats to validity').

Acceptance criteria are fixed BEFORE the measurements (they come from common web-UX guidelines, not from observed numbers):
  C1  single user, read pages          : p95 ≤ 500 ms (small data set) / ≤ 1000 ms (large data set)
  C2  10 concurrent users, mixed browse: p95 ≤ 1000 ms and 0 failed requests
  C3  list pages with the large data set: response ≤ 1.5 MB and single-user time ≤ 1000 ms  (pagination expected)
  C4  database queries per page        : ≤ 30, and the count must not grow with the amount of data (no N+1)

Run twice:  small data set (default seed)  and  large data set (reset_env.sh --big).  Metrics -> results/<cycle>/perf_<dataset>.json
"""
import concurrent.futures as cf
import json
import random
import statistics
import time

import pytest
import requests

from framework import db
from framework.client import AnynClient
from framework.config import APP, PAGES, QLOG, RESULTS_DIR
from framework.tcmeta import nf_case

METRICS = {}


def dataset():
    return "big" if db.scalar("SELECT COUNT(*) FROM gallery") > 1000 else "small"


@pytest.fixture(scope="module", autouse=True)
def _dump_metrics():
    yield
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / f"perf_{dataset()}.json").write_text(json.dumps(METRICS, ensure_ascii=False, indent=1), encoding="utf-8")


def pct(values, p):
    v = sorted(values)
    return v[min(len(v) - 1, int(round(p / 100 * (len(v) - 1))))]


def timed_get(session, url):
    t = time.perf_counter()
    try:
        r = session.get(url, allow_redirects=True, timeout=60)
        return (time.perf_counter() - t) * 1000, r.status_code, len(r.content)
    except Exception:
        return (time.perf_counter() - t) * 1000, 0, 0


PAGES_UNDER_TEST = {
    "home": APP + "/index.php", "home?search": APP + "/index.php?search=aria", "bot_detail": PAGES + "/bot_detail.php?id=1",
    "gallery": PAGES + "/gallery.php", "community_gallery": PAGES + "/community_gallery.php", "ideas": PAGES + "/ideas.php",
    "login": PAGES + "/login.php", "commission": PAGES + "/commission.php",
}


@nf_case("NF-PERF-01", "Performance / Response time", "Thời gian phản hồi một người dùng trên 8 trang chính",
         "Đo p50/p95/max của 30 yêu cầu tuần tự mỗi trang (sau 3 yêu cầu khởi động) — tiêu chí C1",
         ["Khởi động 3 lần", "Gửi 30 yêu cầu GET tuần tự mỗi trang", "Tính percentile"],
         "p95 ≤ 500 ms (dữ liệu nhỏ) / ≤ 1000 ms (dữ liệu lớn); không lỗi HTTP", tool="pytest + requests (time.perf_counter)")
def test_nf_perf_01(ev):
    s = requests.Session()
    limit = 500 if dataset() == "small" else 1000
    out, bad = {}, []
    for name, url in PAGES_UNDER_TEST.items():
        for _ in range(3):
            timed_get(s, url)
        res = [timed_get(s, url) for _ in range(30)]
        lat = [r[0] for r in res]
        errs = sum(1 for r in res if r[1] != 200)
        out[name] = dict(p50=round(pct(lat, 50), 1), p95=round(pct(lat, 95), 1), max=round(max(lat), 1), mean=round(statistics.mean(lat), 1),
                         kb=round(res[0][2] / 1024, 1), errors=errs)
        ev.note(f"[{dataset()}] {name:18s} p50={out[name]['p50']:7.1f} ms  p95={out[name]['p95']:7.1f} ms  max={out[name]['max']:7.1f} ms  {out[name]['kb']:8.1f} KB  lỗi={errs}")
        if out[name]["p95"] > limit or errs:
            bad.append(name)
    METRICS["baseline"] = out
    assert not bad, f"vượt ngưỡng p95 ≤ {limit} ms hoặc có lỗi: {bad}"


@nf_case("NF-PERF-02", "Performance / Load", "Tải đồng thời 1 / 5 / 10 / 20 người dùng duyệt web",
         "Đo throughput và độ trễ khi nhiều người dùng đồng thời (200 yêu cầu/mức, trộn 6 loại trang) — tiêu chí C2",
         ["Với mỗi mức song song: bắn 200 yêu cầu GET ngẫu nhiên theo kịch bản duyệt web", "Ghi throughput, p50/p95/p99, số lỗi"],
         "Tại 10 người dùng: p95 ≤ 1000 ms và 0 lỗi; mức 20 chỉ ghi nhận", tool="pytest + ThreadPoolExecutor (máy chủ PHP 4 worker)")
def test_nf_perf_02(ev):
    mix = ["home", "home?search", "bot_detail", "gallery", "community_gallery", "ideas"]
    random.seed(7)
    levels, rows = {}, []
    for users in (1, 5, 10, 20):
        sessions = [requests.Session() for _ in range(users)]
        jobs = [(sessions[i % users], PAGES_UNDER_TEST[random.choice(mix)]) for i in range(200)]
        t0 = time.perf_counter()
        with cf.ThreadPoolExecutor(users) as ex:
            res = list(ex.map(lambda j: timed_get(*j), jobs))
        wall = time.perf_counter() - t0
        lat = [r[0] for r in res]
        errs = sum(1 for r in res if r[1] != 200)
        levels[users] = dict(throughput=round(len(res) / wall, 1), p50=round(pct(lat, 50), 1), p95=round(pct(lat, 95), 1), p99=round(pct(lat, 99), 1), errors=errs)
        ev.note(f"[{dataset()}] {users:2d} người dùng: {levels[users]['throughput']:6.1f} req/s | p50={levels[users]['p50']:7.1f} | p95={levels[users]['p95']:7.1f} | p99={levels[users]['p99']:7.1f} ms | lỗi={errs}")
    METRICS["load"] = levels
    assert levels[10]["errors"] == 0 and levels[10]["p95"] <= 1000, f"mức 10 người dùng: {levels[10]}"


@nf_case("NF-PERF-03", "Performance / Scalability", "Trang danh sách với khối lượng dữ liệu lớn (phân trang)",
         "Kiểm tra dung lượng phản hồi và thời gian của các trang danh sách khi dữ liệu tăng — tiêu chí C3",
         ["Đếm số dòng dữ liệu của gallery, community_posts, ideas, bots, comments", "Tải từng trang danh sách 5 lần, đo dung lượng và thời gian"],
         "Mỗi trang ≤ 1,5 MB và ≤ 1000 ms ở dữ liệu lớn (kỳ vọng có phân trang)", tool="pytest + requests", bug=["BUG-019"])
def test_nf_perf_03(ev):
    rows = {t: db.scalar(f"SELECT COUNT(*) FROM {t}") for t in ("gallery", "community_posts", "ideas", "bots", "comments")}
    ev.note(f"[{dataset()}] số dòng dữ liệu: {rows}")
    s = requests.Session()
    out, bad = {}, []
    for name in ("home", "gallery", "community_gallery", "ideas"):
        res = [timed_get(s, PAGES_UNDER_TEST[name]) for _ in range(5)]
        t, kb = statistics.median(r[0] for r in res), res[0][2] / 1024
        out[name] = dict(median_ms=round(t, 1), kb=round(kb, 1))
        ev.note(f"[{dataset()}] {name:18s} {kb:9.1f} KB, trung vị {t:8.1f} ms")
        if dataset() == "big" and (kb > 1536 or t > 1000):
            bad.append(f"{name}: {kb:.0f} KB / {t:.0f} ms")
    METRICS["volume"] = dict(rows=rows, pages=out)
    if dataset() == "small":
        pytest.skip("Chạy lại với dữ liệu lớn (reset_env.sh --big) để đánh giá — BLOCKED: cần bộ dữ liệu lớn")
    assert not bad, f"trang danh sách không phân trang, vượt ngưỡng: {bad}"


@nf_case("NF-PERF-04", "Performance / Database", "Số truy vấn CSDL trên mỗi yêu cầu và N+1",
         "Đọc nhật ký truy vấn của lớp tương thích để đếm số truy vấn mỗi trang — tiêu chí C4",
         ["Ghi vị trí cuối của nhật ký truy vấn", "Tải 10 trang (khách) và lấy số truy vấn của yêu cầu tương ứng", "So sánh trang gallery/community giữa hai bộ dữ liệu (lưu trong perf_*.json)"],
         "Mỗi trang ≤ 30 truy vấn; số truy vấn không tăng theo lượng dữ liệu", tool="pytest + ANYN_QLOG (shim)")
def test_nf_perf_04(ev):
    s = requests.Session()
    pages = dict(PAGES_UNDER_TEST, register=PAGES + "/register.php", shop_guest=PAGES + "/shop.php", about=APP + "/index.php?page=1")
    counts = {}
    for name, url in pages.items():
        with open(QLOG, "a+") as f:
            f.seek(0, 2)
            pos = f.tell()
        s.get(url, allow_redirects=False, timeout=60)
        time.sleep(0.15)
        with open(QLOG) as f:
            f.seek(pos)
            lines = [l.rstrip("\n").split("\t") for l in f.readlines() if l.strip()]
        if lines:
            counts[name] = int(lines[-1][4])
            ev.note(f"[{dataset()}] {name:18s} {counts[name]:3d} truy vấn, thời gian SQL {lines[-1][5]} ms / tổng {lines[-1][6]} ms")
    METRICS["queries"] = counts
    worst = {k: v for k, v in counts.items() if v > 30}
    assert counts and not worst, f"trang vượt 30 truy vấn: {worst}"
