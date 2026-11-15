"""Small HTTP client that behaves like a browser session (cookies + CSRF token handling)."""
import itertools
import re
import time
import uuid

import requests
from html.parser import HTMLParser

from . import db
from .config import APP, PAGES, SEED_PASSWORD

_TOKEN_RE = re.compile(r'name="csrf_token"\s+value="([a-f0-9]{64})"')
_counter = itertools.count(1)


def uniq(prefix="u"):
    return f"{prefix}{int(time.time()) % 100000}{next(_counter)}{uuid.uuid4().hex[:4]}"


def strip_tags(html: str) -> str:
    html = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    return re.sub(r"\s+", " ", re.sub(r"(?s)<[^>]+>", " ", html)).strip()


class _FormParser(HTMLParser):
    """Collect the successful controls of one <form> like a browser would (no buttons, unchecked boxes skipped)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.fields = {}
        self._select = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        name = a.get("name")
        if tag == "input" and name:
            t = (a.get("type") or "text").lower()
            if t in ("button", "submit", "image", "reset", "file"):
                return
            if t in ("checkbox", "radio") and "checked" not in a:
                return
            self.fields[name] = a.get("value", "on" if t in ("checkbox", "radio") else "")
        elif tag == "textarea" and name:
            self.fields.setdefault(name, "")
        elif tag == "select" and name:
            self._select = name
        elif tag == "option" and self._select and (("selected" in a) or self._select not in self.fields):
            self.fields[self._select] = a.get("value", "")

    def handle_endtag(self, tag):
        if tag == "select":
            self._select = None


class AnynClient:
    def __init__(self):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = "anyn-qa-harness/1.0"
        self.user_id = None
        self.email = None
        self.password = None
        self.username = None

    # ---- raw requests -------------------------------------------------
    def url(self, path):
        if path.startswith("http"):
            return path
        if path.startswith("/"):
            return APP.rsplit("/anyn", 1)[0] + path
        return PAGES + "/" + path if not path.startswith(("index.php", "search_suggestions")) else APP + "/" + path

    def get(self, path, allow_redirects=False, **kw):
        return self.s.get(self.url(path), allow_redirects=allow_redirects, timeout=30, **kw)

    def token(self, page="login.php"):
        r = self.get(page, allow_redirects=True)
        m = _TOKEN_RE.search(r.text)
        if not m:   # logged-in users are redirected away from login.php: use a page that always has a form
            r = self.get("profile.php", allow_redirects=True)
            m = _TOKEN_RE.search(r.text)
        return m.group(1) if m else ""

    def post(self, path, data=None, files=None, token_page=None, csrf=True, allow_redirects=False, **kw):
        data = dict(data or {})
        if csrf and "csrf_token" not in data:
            data["csrf_token"] = self.token(token_page or path)
        return self.s.post(self.url(path), data=data, files=files, allow_redirects=allow_redirects, timeout=60, **kw)

    # ---- account helpers ----------------------------------------------
    def register(self, username, email, password, confirm=None):
        return self.post("register.php", {"username": username, "email": email, "password": password,
                                          "password_confirm": password if confirm is None else confirm})

    def login(self, email, password=SEED_PASSWORD, remember=False):
        d = {"email": email, "password": password}
        if remember:
            d["remember"] = "1"
        r = self.post("login.php", d)
        if r.status_code in (301, 302):
            m = db.one("SELECT id, username FROM users WHERE email = ?", (email.lower(),))
            if m:
                self.user_id, self.username = m["id"], m["username"]
            self.email, self.password = email, password
        return r

    def logout(self):
        r = self.get("logout.php")
        self.user_id = None
        return r

    @classmethod
    def new_user(cls, prefix="qa", spent=0, gems=0):
        """Register + log in a brand new account (unique name/e-mail) and return the client."""
        c = cls()
        name = uniq(prefix)
        email = f"{name}@qa.test"
        pw = "Passw0rd!x"
        r = c.register(name, email, pw)
        assert "Account created" in r.text, f"fixture: registration failed: {strip_tags(r.text)[:200]}"
        c.login(email, pw)
        assert c.user_id, "fixture: login failed"
        if spent:
            db.run("UPDATE users SET total_spent=? WHERE id=?", (spent, c.user_id))
        if gems:
            db.set_gems(c.user_id, gems)
        c.username, c.email, c.password = name, email, pw
        return c

    @classmethod
    def as_(cls, account):
        c = cls()
        r = c.login(account["email"], account["password"])
        assert r.status_code in (301, 302) and c.user_id, f"fixture: cannot log in as {account['email']}: {r.status_code}"
        return c

    # ---- browser-like form submission -----------------------------------
    def submit_form(self, path, marker, overrides=None, files=None, allow_redirects=False):
        """Do what a real browser does: GET the page, locate the <form> that contains `marker`, and POST exactly the
        fields that form contains (hidden inputs included, any CSRF token the page does NOT put in the form is NOT
        added). Unlike post(), this exposes defects where the rendered form itself is broken."""
        html = self.get(path, allow_redirects=True).text
        form = None
        for m in re.finditer(r"(?is)<form\b[^>]*>.*?</form>", html):
            if marker in m.group(0):
                form = m.group(0)
                break
        assert form, f"no <form> containing {marker!r} on {path}"
        parser = _FormParser()
        parser.feed(form)
        data = dict(parser.fields)
        data.update(overrides or {})
        return self.s.post(self.url(path), data=data, files=files, allow_redirects=allow_redirects, timeout=60), parser.fields

    # ---- convenience ---------------------------------------------------
    def text(self, path):
        return strip_tags(self.get(path, allow_redirects=True).text)
