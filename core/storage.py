import json
import os
from pathlib import Path

DATA_DIR = Path(os.environ.get("CRUMB_DIR", Path.home() / ".config" / "crumb"))
DATA_FILE = DATA_DIR / "crumbs.json"


def load() -> list[dict]:
    if not DATA_FILE.exists():
        return []
    try:
        return json.loads(DATA_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return []


def save(crumbs: list[dict]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = DATA_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(crumbs, indent=2))
    tmp.replace(DATA_FILE)


def next_id(crumbs: list[dict]) -> int:
    return max((c["id"] for c in crumbs), default=0) + 1
