# Agent Instructions

## Scope

Use this file when connecting the module to a `johny-bot-clean`-like Telegram content bot.

## Goal

Add a `twitter` semantic topic that:

- generates one Twitter/X-ready draft from text or caption;
- stores the draft in the host project's normal post table/workflow;
- publishes only after an authorized admin clicks `twitter_publish`;
- never prints or commits Twitter/X credentials.

## Required Reading

1. `README.md`
2. `docs/AGENT_PLAYBOOK_RU.md`
3. `docs/INTEGRATION_PATCHES_RU.md`
4. `docs/DEBUGGING_RU.md`

## Integration Rules

- Make minimal target-project changes: config, router, helpers, setup, keyboards, main.
- Copy runtime files from `integration/johny_bot_clean/` only when the host has matching boundaries.
- If the host differs, reuse `src/johny_twitter_branch/publisher.py` and `prompts/twitter_post.md`, then adapt the handler.
- Do not create automatic publishing from incoming Telegram messages.
- Do not expose secret values in logs, test output or final reports.
- Prefer Telegram aliases such as `@username` or `https://t.me/...` for users/groups in instructions. Do not ask the user for numeric Telegram user/channel IDs as the primary setup format.
- Topic `message_thread_id` may be captured by `/setup_topics` or `/set_topic twitter`; the user should not need to paste it manually.

## Verification

Run, at minimum:

```bash
python -m compileall -q src tests
python -m pytest -q tests/test_twitter.py
python -m johny_twitter_branch doctor --target /path/to/target
```

Only run live auth smoke after credentials are configured:

```bash
python -m johny_twitter_branch smoke-auth --env /path/to/target/.env
```

This smoke test must not publish anything.

