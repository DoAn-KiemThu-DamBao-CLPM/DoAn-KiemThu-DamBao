"""Chạy mỗi script 3 lần và in bảng kết quả để điền vào sheet 'Automation'.

Dùng:  python run_3_times.py
Kết quả: evidence/results.csv  (Lần 1/2/3, thời gian, ngày chạy) + video/ảnh trong evidence/artifacts
"""
import csv
import datetime as dt
import subprocess
import sys
import time
from pathlib import Path

SCRIPTS = [
    ("AT01", "TC004", "tests/test_login_success.py"),
    ("AT02", "TC006", "tests/test_login_lockout.py"),
    ("AT03", "TC014", "tests/test_guest_admin_block.py"),
    ("AT04", "TC089", "tests/test_comment_xss.py"),
    ("AT05", "TC036", "tests/test_submit_idea.py"),
    ("AT06", "TC064", "tests/test_shop_insufficient_gems.py"),
]
RUNS = 3
out_dir = Path("evidence")
out_dir.mkdir(exist_ok=True)

rows = []
for at_id, tc_id, script in SCRIPTS:
    results, total = [], 0.0
    for n in range(1, RUNS + 1):
        t0 = time.time()
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", script, f"--output=evidence/artifacts/{at_id}_run{n}"],
            capture_output=True, text=True,
        )
        total += time.time() - t0
        (out_dir / f"{at_id}_run{n}.log").write_text(proc.stdout + proc.stderr, encoding="utf-8")
        results.append("Pass" if proc.returncode == 0 else "Fail")
    rows.append([at_id, tc_id, script, *results, round(total / RUNS, 1),
                 dt.date.today().strftime("%d/%m/%Y")])
    print(f"{at_id} {tc_id}: {results}  (TB {rows[-1][6]}s)")

with open(out_dir / "results.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["AT ID", "TC ID", "File script", "Lần 1", "Lần 2", "Lần 3", "Thời gian TB (s)", "Ngày chạy"])
    w.writerows(rows)
print("\nĐã ghi evidence/results.csv")
