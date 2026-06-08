## Technology Map
- Runtime/Platform: Python 3.11+, Telegram content bot host, Twitter/X API v2.
- Core Stack: stdlib OAuth 1.0a publisher, Markdown prompt, CLI diagnostics, johny-bot-clean integration templates.
- Components and Responsibilities: `publisher.py` signs and sends X API requests only from explicit publish flows; `prompts/twitter_post.md` constrains generation; `integration/johny_bot_clean/` contains files to copy into a compatible host, including the `draft -> publishing -> published` guard; `docs/` guides the user and coding agent.
- Why This Stack: the module stays dependency-light, reviewable by an AI agent, and easy to graft into bots that already have Telegram routing, AI text generation and draft storage.

# Johny Twitter Branch Module

GitHub-ready module for adding a `Twitter` forum branch to a `johny-bot-clean`-like Telegram content bot.

The branch accepts source text in a Telegram topic, generates one Twitter/X-ready draft, stores it in the host bot workflow and publishes it only after an admin clicks the inline publish button.

Generation, regeneration, revision and model-selection actions do not call Twitter/X API. The host integration must call X only from the explicit `twitter_publish` callback after atomically moving the draft from `draft` to `publishing`; repeated callback deliveries must stop before `TwitterPublisher.publish()`.

## What Is Included

- Portable Twitter/X API v2 publisher with OAuth 1.0a user-context signing.
- English-only `twitter_post` prompt for one post up to 280 characters.
- Integration files for a host project shaped like `johny-bot-clean`.
- Idempotency guard pattern for host storage: `draft -> publishing -> published`.
- Agent playbook and user setup docs in Russian.
- CLI:
  - `guide` prints the installation sequence.
  - `doctor --target /path/to/project` checks whether the host is wired.
  - `smoke-auth --env /path/to/.env` verifies X credentials without publishing.

## Quick Start For An Agent

```bash
git clone <this-repo-url>
cd johny-twitter-branch-module
python -m johny_twitter_branch guide
python -m johny_twitter_branch doctor --target /path/to/johny-bot-clean
```

If the server does not have a `python` binary, use `python3` for the same commands.

Then follow [docs/AGENT_PLAYBOOK_RU.md](docs/AGENT_PLAYBOOK_RU.md) and [docs/INTEGRATION_PATCHES_RU.md](docs/INTEGRATION_PATCHES_RU.md).

## Quick Start For A User

1. Create an X developer app at `https://console.x.com/`.
2. Enable app permissions that allow writing posts.
3. Generate and save:
   - `TWITTER_API_KEY`
   - `TWITTER_API_SECRET`
   - `TWITTER_ACCESS_TOKEN`
   - `TWITTER_ACCESS_TOKEN_SECRET`
4. Give these values to the target project only through `.env` or a secret manager.
5. In Telegram, create or bind the topic with `/setup_topics` or `/set_topic twitter`.
6. Send source text into the `Twitter` topic and approve publication manually.

Full user guide: [docs/USER_SETUP_RU.md](docs/USER_SETUP_RU.md).

## Host Project Contract

The target project should already have:

- `python-telegram-bot` based update routing.
- A `PostGenerator` or compatible service with `generate_post(source, prompt_name=..., style_prompt_name=...)`.
- A draft storage model similar to `create_post`, `get_post_by_message_id`, `get_latest_revision_for_post`, `update_post_status`.
- An atomic status helper like `mark_post_publishing(post_id)` that succeeds only once for `draft -> publishing`.
- A topic setup flow similar to `/setup_topics` and `/set_topic`.
- Runtime `context.bot_data` with text AI clients and config.

If the host differs, keep `src/johny_twitter_branch/publisher.py` and `prompts/twitter_post.md`, then adapt only the Telegram handler boundary.

## Environment

Copy from [.env.example](.env.example):

```env
TWITTER_API_KEY=
TWITTER_API_SECRET=
TWITTER_ACCESS_TOKEN=
TWITTER_ACCESS_TOKEN_SECRET=
TWITTER_API_BASE_URL=https://api.x.com
TOPIC_TWITTER=0
```

Do not commit real credentials. For Telegram users/groups, prefer `@username` or `https://t.me/...` aliases in project instructions; use topic commands to capture `message_thread_id`.

## Verification

```bash
python -m compileall -q src tests
python -m pytest -q
python -m johny_twitter_branch doctor --target /path/to/target
python -m johny_twitter_branch smoke-auth --env /path/to/target/.env
```

`smoke-auth` performs a safe auth check and does not create a post.

Runtime X API calls are limited to explicit publication. Sending source text to the Telegram topic, editing a draft, switching a model or regenerating a draft must not call X.

## Official X Docs Checked

Checked on 2026-06-05:

- Getting access: https://docs.x.com/x-api/getting-started/getting-access
- Developer Console: https://docs.x.com/resources/fundamentals/developer-portal
- Create Post endpoint: https://docs.x.com/x-api/posts/create-post
- Manage Posts quickstart: https://docs.x.com/x-api/posts/manage-tweets/quickstart
- OAuth 1.0a credentials: https://docs.x.com/fundamentals/authentication/oauth-1-0a/api-key-and-secret
