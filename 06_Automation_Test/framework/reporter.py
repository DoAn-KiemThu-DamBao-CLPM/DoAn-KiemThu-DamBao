"""pytest plugin: collect one record per executed test case and dump JSON/CSV for the reports."""
import json
import time
from pathlib import Path

import pytest

from .config import CYCLE, RESULTS_DIR
from .tcmeta import REGISTRY, UI_REGISTRY, NF_REGISTRY

_records = {}
_ui_records = {}
_nf_records = {}


class Evidence:
    """Per-test evidence collector (injected through the `ev` fixture)."""

    def __init__(self):
        self.lines = []
        self.screens = []

    def note(self, text):
        self.lines.append(str(text))

    def http(self, label, resp, snippet=None):
        loc = resp.headers.get("Location")
        line = f"{label}: HTTP {resp.status_code}" + (f" -> {loc}" if loc else "")
        if snippet:
            line += f" | {snippet}"
        self.lines.append(line)


@pytest.fixture
def ev(request):
    e = Evidence()
    request.node._ev = e
    return e


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    fn = getattr(item, "function", None)
    tc_id = getattr(fn, "tc_id", None)
    store = _records
    if tc_id is None:
        tc_id = getattr(fn, "ui_id", None)
        store = _ui_records
    if tc_id is None:
        tc_id = getattr(fn, "nf_id", None)
        store = _nf_records
    if tc_id is None:
        return
    rec = store.setdefault(tc_id, {"id": tc_id, "status": "Not Run", "actual": "", "duration": 0.0})
    ev = getattr(item, "_ev", None)
    rec["duration"] += getattr(rep, "duration", 0.0)
    if rep.when == "call":
        if rep.passed:
            rec["status"] = "Pass"
        elif rep.failed:
            rec["status"] = "Fail"
            msg = rep.longrepr.reprcrash.message if hasattr(rep.longrepr, "reprcrash") and rep.longrepr.reprcrash else str(rep.longrepr)
            rec["actual"] = msg.replace("AssertionError: ", "")[:1500]
        elif rep.skipped:
            reason = str(rep.longrepr[2]) if isinstance(rep.longrepr, tuple) else str(rep.longrepr)
            rec["status"] = "Blocked" if "BLOCKED" in reason else "Not Run"
            rec["actual"] = reason.replace("Skipped: ", "")
    elif rep.when == "setup" and rep.failed:
        rec["status"] = "Blocked"
        rec["actual"] = "Set-up failed: " + str(rep.longrepr)[-400:]
    elif rep.when == "setup" and rep.skipped:
        reason = str(rep.longrepr[2]) if isinstance(rep.longrepr, tuple) else str(rep.longrepr)
        rec["status"] = "Blocked" if "BLOCKED" in reason else "Not Run"
        rec["actual"] = reason.replace("Skipped: ", "")
    if ev:
        rec["evidence"] = ev.lines
        rec["screens"] = ev.screens


def _merge_write(path, new_records):
    """Merge by id with an existing results file so that partial runs never wipe other suites' results."""
    old = {}
    if path.exists():
        try:
            old = {r["id"]: r for r in json.loads(path.read_text(encoding="utf-8"))}
        except Exception:
            old = {}
    for r in new_records:
        old[r["id"]] = r
    path.write_text(json.dumps([old[k] for k in sorted(old)], ensure_ascii=False, indent=1), encoding="utf-8")


def pytest_sessionfinish(session, exitstatus):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    if _ui_records:
        ui_out = []
        for uid, rec in sorted(_ui_records.items()):
            meta = UI_REGISTRY.get(uid, {})
            rec["executed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            rec["implements"] = meta.get("implements")
            rec["bug"] = meta.get("bug", [])
            ui_out.append(rec)
        _merge_write(Path(RESULTS_DIR / "ui_results.json"), ui_out)
    if _nf_records:
        nf_out = []
        for nid, rec in sorted(_nf_records.items()):
            meta = NF_REGISTRY.get(nid, {})
            rec["executed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            rec["category"] = meta.get("category")
            rec["bug"] = meta.get("bug", [])
            nf_out.append(rec)
        _merge_write(Path(RESULTS_DIR / "nonfunctional_results.json"), nf_out)
    if not _records:
        return
    out = []
    for tc_id, rec in sorted(_records.items()):
        meta = REGISTRY.get(tc_id, {})
        rec["executed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        rec["bug"] = meta.get("bug", [])
        out.append(rec)
    _merge_write(Path(RESULTS_DIR / "execution_results.json"), out)
