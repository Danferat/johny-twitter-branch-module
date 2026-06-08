"""Host-project diagnostics for the Twitter/X branch integration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from johny_twitter_branch.constants import (
    HOST_PATCH_POINTS,
    HOST_RUNTIME_FILES,
    REQUIRED_SECRET_FIELDS,
)


@dataclass(frozen=True)
class Check:
    """One diagnostic check result."""

    name: str
    ok: bool
    detail: str


def parse_env_file(path: Path) -> dict[str, str]:
    """Parse a small dotenv-like file without external dependencies."""
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in {"'", '"'}
        ):
            value = value[1:-1]
        values[key.strip()] = value
    return values


def secret_status(values: dict[str, str]) -> list[Check]:
    """Return SET/MISSING checks without exposing secret values."""
    checks: list[Check] = []
    for field in REQUIRED_SECRET_FIELDS:
        is_set = bool(values.get(field, "").strip())
        checks.append(
            Check(
                name=field,
                ok=is_set,
                detail="SET" if is_set else "MISSING",
            )
        )
    return checks


def inspect_target(target: Path) -> list[Check]:
    """Inspect a johny-bot-clean-like target project for integration markers."""
    checks: list[Check] = []
    checks.extend(_runtime_file_checks(target))
    checks.extend(_patch_marker_checks(target))
    checks.extend(_env_example_checks(target))
    checks.extend(_env_checks(target))
    return checks


def all_required_ok(checks: Iterable[Check]) -> bool:
    """Return True when all checks passed."""
    return all(check.ok for check in checks)


def format_checks(checks: Iterable[Check]) -> str:
    """Render checks as a terminal-friendly report."""
    lines = []
    for check in checks:
        mark = "OK" if check.ok else "MISS"
        lines.append(f"[{mark}] {check.name}: {check.detail}")
    return "\n".join(lines)


def _runtime_file_checks(target: Path) -> list[Check]:
    checks: list[Check] = []
    for relative in HOST_RUNTIME_FILES:
        path = target / relative
        checks.append(
            Check(
                name=relative,
                ok=path.exists(),
                detail="present" if path.exists() else "copy from integration files",
            )
        )
    return checks


def _patch_marker_checks(target: Path) -> list[Check]:
    markers = {
        "src/config.py": (
            "TWITTER_API_KEY",
            "TWITTER_API_SECRET",
            "TWITTER_ACCESS_TOKEN",
            "TWITTER_ACCESS_TOKEN_SECRET",
            "TOPIC_TWITTER",
        ),
        "src/bot/router.py": ('TWITTER = "twitter"',),
        "src/bot/helpers.py": ('"twitter"',),
        "src/bot/setup.py": ('"twitter": "Twitter"',),
        "src/bot/keyboards.py": (
            "build_twitter_publish_keyboard",
            "twitter_publish",
        ),
        "src/db/models.py": (
            "mark_post_publishing",
            "status = 'publishing'",
        ),
        "src/main.py": (
            "handle_twitter",
            "handle_twitter_publish",
            "twitter_publisher",
            "twitter_publish",
            "TOPIC_TWITTER",
        ),
    }
    checks: list[Check] = []
    for relative in HOST_PATCH_POINTS:
        if relative == ".env.example":
            continue
        path = target / relative
        if not path.exists():
            checks.append(Check(relative, False, "file missing"))
            continue
        text = path.read_text(encoding="utf-8")
        missing = [marker for marker in markers.get(relative, ()) if marker not in text]
        checks.append(
            Check(
                name=relative,
                ok=not missing,
                detail="markers present" if not missing else "missing: " + ", ".join(missing),
            )
        )
    return checks


def _env_example_checks(target: Path) -> list[Check]:
    path = target / ".env.example"
    if not path.exists():
        return [Check(".env.example", False, "file missing")]
    text = path.read_text(encoding="utf-8")
    fields = (
        "TWITTER_API_KEY",
        "TWITTER_API_SECRET",
        "TWITTER_ACCESS_TOKEN",
        "TWITTER_ACCESS_TOKEN_SECRET",
        "TOPIC_TWITTER",
    )
    missing = [field for field in fields if field not in text]
    return [
        Check(
            ".env.example",
            ok=not missing,
            detail="Twitter fields present" if not missing else "missing: " + ", ".join(missing),
        )
    ]


def _env_checks(target: Path) -> list[Check]:
    path = target / ".env"
    if not path.exists():
        return [Check(".env", False, "missing; create from .env.example")]
    values = parse_env_file(path)
    checks = secret_status(values)
    topic_raw = values.get("TOPIC_TWITTER", "")
    topic_ok = topic_raw.isdigit() and int(topic_raw) > 0
    checks.append(
        Check(
            "TOPIC_TWITTER",
            topic_ok,
            "SET" if topic_ok else "MISSING/0; use /setup_topics or /set_topic twitter",
        )
    )
    return checks
