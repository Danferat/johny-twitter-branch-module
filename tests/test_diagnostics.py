from __future__ import annotations

from pathlib import Path

from johny_twitter_branch.diagnostics import (
    all_required_ok,
    inspect_target,
    parse_env_file,
    secret_status,
)


def test_parse_env_file_handles_quotes(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "TWITTER_API_KEY='abc'",
                'TWITTER_API_SECRET="def"',
                "IGNORED_LINE",
                "# comment",
            ]
        ),
        encoding="utf-8",
    )

    values = parse_env_file(env_path)

    assert values["TWITTER_API_KEY"] == "abc"
    assert values["TWITTER_API_SECRET"] == "def"


def test_secret_status_does_not_expose_values() -> None:
    checks = secret_status(
        {
            "TWITTER_API_KEY": "abc",
            "TWITTER_API_SECRET": "def",
        }
    )
    report = "\n".join(check.detail for check in checks)

    assert "abc" not in report
    assert "def" not in report
    assert "SET" in report
    assert "MISSING" in report


def test_inspect_target_reports_missing_files(tmp_path: Path) -> None:
    checks = inspect_target(tmp_path)

    assert not all_required_ok(checks)
    assert any(check.name == "src/bot/twitter.py" and not check.ok for check in checks)

