"""Test-case metadata.

Every executable test carries the *specification* of the manual test case it implements
(@tc decorator).  The Test Case Specification (xlsx/docx) is generated from the same registry,
so spec and execution can never drift apart.
"""
REGISTRY = {}


def tc(id, ts, fr, title, pre, steps, data, expected, technique, kind="Valid", priority="Medium",
       auto="Script", bug=None, ui=None):
    def deco(fn):
        REGISTRY[id] = dict(id=id, ts=ts, fr=fr, title=title, pre=pre, steps=steps, data=data,
                            expected=expected, technique=technique, kind=kind, priority=priority,
                            auto=auto, bug=bug or [], ui=ui, func=fn.__name__, module=fn.__module__)
        fn.tc_id = id
        return fn
    return deco


UI_REGISTRY = {}


def ui_case(id, implements, title, steps, expected, bug=None):
    """Browser-level (Playwright) automated case.  It re-checks, through the real UI, a case that is also
    specified/executed at HTTP level (`implements` = TC id)."""
    def deco(fn):
        UI_REGISTRY[id] = dict(id=id, implements=implements, title=title, steps=steps, expected=expected,
                               bug=bug or [], func=fn.__name__, module=fn.__module__)
        fn.ui_id = id
        return fn
    return deco


NF_REGISTRY = {}


def nf_case(id, category, title, objective, steps, criteria, tool="pytest + requests", bug=None):
    """Non-functional test (security / performance / usability)."""
    def deco(fn):
        NF_REGISTRY[id] = dict(id=id, category=category, title=title, objective=objective, steps=steps,
                               criteria=criteria, tool=tool, bug=bug or [], func=fn.__name__, module=fn.__module__)
        fn.nf_id = id
        return fn
    return deco
