"""Central configuration of the test framework (override with environment variables)."""
import os
from pathlib import Path

BASE_URL = os.environ.get("ANYN_BASE_URL", "http://127.0.0.1:8765").rstrip("/")
APP = BASE_URL + "/anyn"
PAGES = APP + "/pages"
DB_FILE = os.environ.get("ANYN_SQLITE", str(Path.home() / "anyn_qa_runtime" / "anyn.sqlite"))
UPLOAD_DIR = os.environ.get("ANYN_UPLOAD_DIR", str(Path.home() / "anyn_qa_runtime" / "sut" / "anyn" / "uploads"))
QLOG = os.environ.get("ANYN_QLOG", str(Path.home() / "anyn_qa_runtime" / "queries.log"))

# fixture accounts created by test_environment/tools/seed.py
SEED_PASSWORD = os.environ.get("SEED_PASSWORD", "User@12345")
ADMIN = {"email": "admin@anyn.test", "password": SEED_PASSWORD, "id": 1}
ALICE = {"email": "alice@anyn.test", "password": SEED_PASSWORD, "id": 2}
BOB = {"email": "bob@anyn.test", "password": SEED_PASSWORD, "id": 3}
CAROL = {"email": "carol@anyn.test", "password": SEED_PASSWORD, "id": 4}   # premium (total_spent = 25)

CYCLE = os.environ.get("QA_CYCLE", "cycle1")
RESULTS_DIR = Path(os.environ.get("QA_RESULTS_DIR", Path(__file__).resolve().parent.parent / "results")) / CYCLE
