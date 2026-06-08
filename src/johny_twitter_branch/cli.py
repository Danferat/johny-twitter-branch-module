"""Command-line guide and diagnostics for the Twitter/X branch module."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from johny_twitter_branch.diagnostics import (
    all_required_ok,
    format_checks,
    inspect_target,
    parse_env_file,
    secret_status,
)
from johny_twitter_branch.publisher import TwitterPublishError, TwitterPublisher


GUIDE_TEXT = """Johny Twitter/X branch integration

Agent checklist:
1. Copy integration/johny_bot_clean/src/bot/twitter.py to target src/bot/twitter.py.
2. Copy integration/johny_bot_clean/src/services/twitter_publisher.py to target src/services/twitter_publisher.py.
3. Copy prompts/twitter_post.md to target src/prompts/twitter_post.md.
4. Patch target config/router/helpers/setup/keyboards/db/main using docs/INTEGRATION_PATCHES_RU.md.
5. Add .env fields from .env.example. Do not print or commit secrets.
6. In Telegram, create or bind the forum topic with /setup_topics or /set_topic twitter.
7. Confirm X API is reachable only from twitter_publish after draft -> publishing lock.
8. Run compileall, targeted pytest, then doctor.
9. Run smoke-auth only after the user confirms credentials are present.

User checklist:
1. Create an X developer app at https://console.x.com/.
2. Enable Read and Write permissions.
3. Generate API Key/Secret and Access Token/Secret for the account that will post.
4. Put the four values into the target project's .env.
5. Send text into the Telegram topic named Twitter.
6. Review the draft and click the publish button only when ready.
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="johny-twitter-branch",
        description="Guide and diagnostics for the Johny Twitter/X branch module.",
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("guide", help="print integration steps")

    doctor = subparsers.add_parser(
        "doctor",
        help="inspect a johny-bot-clean-like target project",
    )
    doctor.add_argument(
        "--target",
        type=Path,
        default=Path("."),
        help="target project root",
    )

    smoke = subparsers.add_parser(
        "smoke-auth",
        help="verify X API credentials without publishing",
    )
    smoke.add_argument(
        "--env",
        type=Path,
        default=Path(".env"),
        help="path to target .env",
    )

    args = parser.parse_args(argv)
    if args.command in {None, "guide"}:
        print(GUIDE_TEXT)
        return 0
    if args.command == "doctor":
        return _doctor(args.target)
    if args.command == "smoke-auth":
        return _smoke_auth(args.env)
    parser.print_help()
    return 2


def _doctor(target: Path) -> int:
    checks = inspect_target(target.resolve())
    print(format_checks(checks))
    return 0 if all_required_ok(checks) else 1


def _smoke_auth(env_path: Path) -> int:
    values = parse_env_file(env_path)
    checks = secret_status(values)
    print(format_checks(checks))
    if not all_required_ok(checks):
        print("TWITTER_AUTH_OK=False")
        return 1

    publisher = TwitterPublisher.from_env(values)
    try:
        result = asyncio.run(publisher.verify_credentials())
    except TwitterPublishError as exc:
        print("TWITTER_AUTH_OK=False")
        print(f"ERROR={exc}")
        return 1

    print("TWITTER_AUTH_OK=True")
    if result.handle:
        print(f"USERNAME={result.handle}")
    else:
        print(f"USER_ID={result.user_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
