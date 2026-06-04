
from __future__ import annotations

import json
import logging
import os
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

__version__ = "1.0.0"
__author__ = "Syed Sameer Ul Hassan"
__license__ = "Apache-2.0"

CONFIG_DIR = Path.home() / ".mailspoof"
CONFIG_FILE = CONFIG_DIR / "config.json"
LOG_FILE = CONFIG_DIR / "audit.log"
REPORTS_DIR = CONFIG_DIR / "reports"
TEMPLATES_DIR = CONFIG_DIR / "templates"

@dataclass
class Scenario:
    id: int
    name: str
    category: str
    severity: str
    from_email: str
    from_name: str
    subject: str
    body: str
    description: str = ""
    source: str = "built-in"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class TestResult:
    timestamp: str
    test_type: str
    scenario: str
    target: str
    from_email: str
    success: bool
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

_BUILTINS_DIR = Path(__file__).resolve().parent.parent / "templates" / "builtins"

def load_builtin_templates() -> List[Dict[str, Any]]:
    scenarios: List[Dict[str, Any]] = []
    if not _BUILTINS_DIR.exists():
        return scenarios

    files = sorted(_BUILTINS_DIR.glob("*.txt"))
    for idx, path in enumerate(files, start=1):
        try:
            text = path.read_text(encoding="utf-8")
            text = text.replace("{TODAY}", datetime.now().strftime("%Y-%m-%d"))
            data = _parse_template(text)
            data["id"] = idx
            data["source"] = "built-in"
            scenarios.append(data)
        except Exception as exc:
            logging.warning(f"Failed to load built-in template {path.name}: {exc}")
    return scenarios

_TEMPLATE_KEYS = {
    "name", "category", "severity", "from email", "from name",
    "subject", "body", "description",
}

def load_user_templates(start_id: int = 6) -> List[Dict[str, Any]]:
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    scenarios: List[Dict[str, Any]] = []

    search_paths = [TEMPLATES_DIR]
    local_templates = Path(__file__).resolve().parent.parent / "templates"
    if local_templates.exists() and local_templates != TEMPLATES_DIR:
        search_paths.append(local_templates)

    all_files: List[Path] = []
    for sp in search_paths:
        for p in sorted(sp.glob("*.txt")):
            if "builtins" not in str(p.parent):
                all_files.append(p)

    seen: set[str] = set()
    unique_files: List[Path] = []
    for p in all_files:
        if p.name not in seen:
            seen.add(p.name)
            unique_files.append(p)

    for idx, path in enumerate(unique_files, start=start_id):
        try:
            text = path.read_text(encoding="utf-8")
            has_headers = False
            for line in text.splitlines():
                lower = line.lower().strip()
                for key in _TEMPLATE_KEYS:
                    if lower.startswith(key + ":"):
                        has_headers = True
                        break
                if has_headers:
                    break

            if has_headers:
                data = _parse_template(text)
            else:
                data = {
                    "name": path.stem.replace("_", " ").title(),
                    "category": "Custom",
                    "severity": "User-defined",
                    "from_email": "",
                    "from_name": "",
                    "subject": "",
                    "body": text.strip(),
                    "description": f"Custom body-only template: {path.name}",
                }

            data["id"] = idx
            data["source"] = "custom"
            scenarios.append(data)
        except Exception as exc:
            logging.warning(f"Failed to load user template {path.name}: {exc}")

    return scenarios

def _parse_template(text: str) -> Dict[str, str]:
    lines = text.splitlines()
    result: Dict[str, str] = {}
    current_key: str | None = None
    body_lines: List[str] = []
    in_body = False

    for raw in lines:
        line = raw.rstrip()
        if not line:
            if in_body:
                body_lines.append("")
            continue

        lower = line.lower()
        matched_key = None
        for key in _TEMPLATE_KEYS:
            prefix = key + ":"
            if lower.startswith(prefix):
                matched_key = key
                break

        if matched_key:
            if in_body and matched_key != "description":
                pass
            elif matched_key == "body":
                in_body = True
                current_key = matched_key
                val = line[len(matched_key) + 1:].strip()
                if val:
                    body_lines.append(val)
                continue
            else:
                in_body = False
                current_key = matched_key
                val = line[len(matched_key) + 1:].strip()
                result[current_key] = val
                continue

        if in_body:
            body_lines.append(line)

    if body_lines:
        while body_lines and body_lines[0] == "":
            body_lines.pop(0)
        while body_lines and body_lines[-1] == "":
            body_lines.pop()
        result["body"] = "\n".join(body_lines)

    mapping = {
        "name": "name",
        "category": "category",
        "severity": "severity",
        "from email": "from_email",
        "from name": "from_name",
        "subject": "subject",
        "body": "body",
        "description": "description",
    }
    normalized: Dict[str, str] = {}
    for old_key, new_key in mapping.items():
        normalized[new_key] = result.get(old_key, "")

    normalized.setdefault("description", f"Custom template.")
    normalized.setdefault("severity", "Medium")
    normalized.setdefault("category", "Custom")

    return normalized

class Config:

    def __init__(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
        self.data = self._load()
        self._builtin_templates = load_builtin_templates()
        self._custom_templates = load_user_templates(start_id=len(self._builtin_templates) + 1)
        self._init_logging()

    def _load(self) -> Dict[str, Any]:
        defaults: Dict[str, Any] = {
            "version": __version__,
            "smtp_server": {"host": "0.0.0.0", "port": 2525, "timeout": 30},
            "reporting": {"format": "json", "auto_generate": True},
        }
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r") as fh:
                    loaded = json.load(fh)
                for key, value in defaults.items():
                    loaded.setdefault(key, value)
                return loaded
            except Exception as exc:
                logging.warning(f"Config load failed: {exc}; using defaults")
                return defaults
        else:
            self._save(defaults)
            return defaults

    def _save(self, data: Dict[str, Any]):
        try:
            with open(CONFIG_FILE, "w") as fh:
                json.dump(data, fh, indent=2)
        except Exception as exc:
            logging.warning(f"Config save failed: {exc}")

    def _init_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)s | %(message)s",
            handlers=[
                logging.FileHandler(LOG_FILE),
                logging.StreamHandler(sys.stdout),
            ],
        )
        self.logger = logging.getLogger("MailSpoof")

    def scenarios(self) -> List[Scenario]:
        built_in = [Scenario(**s) for s in self._builtin_templates]
        custom = [Scenario(**s) for s in self._custom_templates]
        return built_in + custom

    def scenario_by_id(self, sid: int) -> Scenario | None:
        for s in self.scenarios():
            if s.id == sid:
                return s
        return None
