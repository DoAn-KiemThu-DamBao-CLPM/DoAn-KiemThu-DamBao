"""Playwright fixtures: one fresh browser context per test, external CDNs blocked (fonts/icons are cosmetic only)."""
import pytest
from playwright.sync_api import sync_playwright

from framework.config import BASE_URL, PAGES, RESULTS_DIR

SHOTS = RESULTS_DIR / "screenshots"


@pytest.fixture(scope="session")
def _pw():
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


@pytest.fixture
def new_page(_pw):
    """factory: new_page(viewport=(w,h)) -> Playwright page.  Contexts are closed after the test."""
    ctxs = []

    def make(viewport=(1280, 800)):
        ctx = _pw.new_context(viewport={"width": viewport[0], "height": viewport[1]}, device_scale_factor=1)
        ctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith(BASE_URL) else r.abort())
        ctxs.append(ctx)
        pg = ctx.new_page()
        pg.set_default_timeout(15000)
        return pg

    yield make
    for c in ctxs:
        c.close()


@pytest.fixture
def shot(ev):
    SHOTS.mkdir(parents=True, exist_ok=True)

    def take(page, name):
        path = SHOTS / f"{name}.png"
        # the site fades cards in (CSS animation, opacity 0 at load): fast-forward finite animations so the evidence shows the final state
        page.screenshot(path=str(path), full_page=False, animations="disabled")
        ev.screens.append(f"screenshots/{name}.png")
        return path

    return take


def ui_login(page, email, password):
    page.goto(PAGES + "/login.php")
    page.fill("input[name=email]", email)
    page.fill("input[name=password]", password)
    page.click("button[type=submit]")
    page.wait_for_load_state()
