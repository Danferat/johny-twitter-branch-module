# System State / CHANGELOG

## 2026-06-05 16:35 UTC — Сжатие без потерь

### Контекст

- Локальный исходный проект: `/root/Projects/Разработка/johny-bot-clean`.
- Выделенный модуль: `/root/Projects/Разработка/johny-twitter-branch-module`.
- GitHub remote: `git@github.com:Danferat/johny-twitter-branch-module.git`.
- GitHub URL: `https://github.com/Danferat/johny-twitter-branch-module`.
- Текущая ветка: `main`.
- Текущий опубликованный commit: `5734cb2 Create Twitter branch module`.
- Цель модуля: дать переносимый пакет для подключения Twitter/X-ветки к проектам, похожим на `johny-bot-clean`, с инструкциями для ИИ-агента и пользователя.

### Проверяемая цель

После подключения модуля к host-проекту должна появиться semantic ветка `twitter` / Telegram topic `Twitter`, которая:

- принимает исходный текст или caption в Telegram forum topic;
- генерирует один англоязычный Twitter/X-ready draft до 280 символов;
- сохраняет draft в стандартное хранилище постов host-проекта;
- показывает inline-кнопку `Опубликовать в Twitter`;
- публикует через Twitter/X API v2 только после явного нажатия админом;
- безопасно блокирует публикацию, если `TWITTER_*` credentials не заполнены;
- не выводит и не коммитит секреты.

### Архитектурные допущения host-проекта

- Python 3.11+.
- Telegram bot на `python-telegram-bot`.
- Включены Telegram forum topics.
- Есть topic setup flow: `/setup_topics`, `/set_topic <тип>`, persisted topic overrides.
- Есть prompt loader с именами prompt-файлов.
- Есть text generation service, совместимый с `PostGenerator.generate_post(source, prompt_name=..., style_prompt_name=...)`.
- Есть draft storage API, совместимое по смыслу с:
  - `create_post`;
  - `get_post_by_message_id`;
  - `get_latest_revision_for_post`;
  - `update_post_status`.
- Есть `context.bot_data` с config, text clients, factory/services.
- Есть callback routing через `CallbackQueryHandler`.

Если host отличается, переносить не весь Telegram handler слепо, а только ядро:

- `src/johny_twitter_branch/publisher.py`;
- `prompts/twitter_post.md`;
- смысл workflow: draft first, manual publish later.

### Файловый состав модуля

- `README.md` — public overview, Technology Map, quick start для агента и пользователя.
- `AGENTS.md` — правила для ИИ-агента при подключении модуля.
- `.env.example` — безопасный шаблон переменных без секретов.
- `.gitignore` — исключает `.env`, cache, build artifacts.
- `pyproject.toml` — package metadata, console script `johny-twitter-branch`.
- `memory.md` — локальная запись о создании модуля и проверках.
- `CHANGELOG.md` — этот System State.
- `prompts/twitter_post.md` — prompt для генерации одного Twitter/X post.
- `docs/AGENT_PLAYBOOK_RU.md` — пошаговый план подключения для агента.
- `docs/USER_SETUP_RU.md` — инструкция для простого пользователя.
- `docs/X_API_KEYS_RU.md` — где взять X API credentials.
- `docs/INTEGRATION_PATCHES_RU.md` — точечные изменения в `johny-bot-clean`-like host.
- `docs/DEBUGGING_RU.md` — диагностика проблем подключения.
- `integration/johny_bot_clean/src/bot/twitter.py` — host handler template.
- `integration/johny_bot_clean/src/services/twitter_publisher.py` — self-contained host publisher template.
- `integration/johny_bot_clean/tests/test_twitter.py` — тесты для host integration.
- `src/johny_twitter_branch/__init__.py` — public exports.
- `src/johny_twitter_branch/__main__.py` — `python -m johny_twitter_branch`.
- `src/johny_twitter_branch/constants.py` — стабильные constants/checklists.
- `src/johny_twitter_branch/publisher.py` — portable OAuth 1.0a publisher + auth smoke.
- `src/johny_twitter_branch/diagnostics.py` — host-project diagnostics.
- `src/johny_twitter_branch/cli.py` — CLI commands.
- `tests/test_publisher.py` — unit tests publisher behavior.
- `tests/test_diagnostics.py` — unit tests diagnostics/env masking.

### Constants / контракты

Из `src/johny_twitter_branch/constants.py`:

- `TOPIC_TYPE = "twitter"`.
- `TOPIC_LABEL = "Twitter"`.
- `PROMPT_NAME = "twitter_post"`.
- `CALLBACK_DATA = "twitter_publish"`.
- `ENV_FIELDS`:
  - `TWITTER_API_KEY`;
  - `TWITTER_API_SECRET`;
  - `TWITTER_ACCESS_TOKEN`;
  - `TWITTER_ACCESS_TOKEN_SECRET`;
  - `TWITTER_API_BASE_URL`;
  - `TOPIC_TWITTER`.
- `REQUIRED_SECRET_FIELDS`:
  - `TWITTER_API_KEY`;
  - `TWITTER_API_SECRET`;
  - `TWITTER_ACCESS_TOKEN`;
  - `TWITTER_ACCESS_TOKEN_SECRET`.
- `HOST_RUNTIME_FILES`:
  - `src/bot/twitter.py`;
  - `src/services/twitter_publisher.py`;
  - `src/prompts/twitter_post.md`.
- `HOST_PATCH_POINTS`:
  - `src/config.py`;
  - `src/bot/router.py`;
  - `src/bot/helpers.py`;
  - `src/bot/setup.py`;
  - `src/bot/keyboards.py`;
  - `src/main.py`;
  - `.env.example`.

### Environment contract

Required for live publishing:

```env
TWITTER_API_KEY=
TWITTER_API_SECRET=
TWITTER_ACCESS_TOKEN=
TWITTER_ACCESS_TOKEN_SECRET=
```

Optional/default:

```env
TWITTER_API_BASE_URL=https://api.x.com
TOPIC_TWITTER=0
```

Rules:

- `TOPIC_TWITTER=0` is acceptable before `/setup_topics` or `/set_topic twitter`.
- Do not persist `"twitter": 0` in topic override JSON if the host treats overrides as higher priority than `.env`.
- Do not print secret values. Diagnostics may print only `SET` / `MISSING`.
- For Telegram users/groups in instructions, prefer `@username` or `https://t.me/...`; do not use numeric Telegram IDs as the primary user-facing setup format.

### Publisher API

File: `src/johny_twitter_branch/publisher.py`.

Classes:

- `TwitterPublishError(Exception)` — thrown for missing credentials, invalid text, HTTP/network/API response errors.
- `TwitterPublishResult`:
  - fields: `post_id`, `text`, `public_post_base_url`;
  - property `tweet_id` — backward-compatible alias for `post_id`;
  - property `url` — public post URL, default `https://x.com/i/web/status/<post_id>`.
- `TwitterAuthResult`:
  - fields: `user_id`, `username`, `name`;
  - property `handle` — returns `@username` if present.
- `TwitterPublisher`:
  - constructor fields: `api_key`, `api_secret`, `access_token`, `access_token_secret`, `api_base_url`, `public_post_base_url`;
  - classmethod `from_env(values=None)`;
  - property `is_configured`;
  - async `publish(text)`;
  - async `verify_credentials()`;
  - internal `_publish_sync(text)`;
  - internal `_verify_credentials_sync()`;
  - internal `_request_json(method, path, payload=None)`;
  - internal `_url(path)`;
  - internal `_build_oauth_header(method, url)`;
  - internal `_sign(method, url, oauth_params)`.

Low-level helpers:

- `_quote(value)`;
- `_canonical_url_and_query_params(url)`.

Behavior:

- Uses OAuth 1.0a HMAC-SHA1 user-context credentials.
- `publish()` validates credentials before network work.
- `publish()` rejects empty text.
- `publish()` rejects text longer than 280 characters.
- `verify_credentials()` runs safe GET auth smoke test and does not publish.
- Default create endpoint path: `/2/tweets`.
- Default verify endpoint path: `/2/users/me?user.fields=username`.
- Default API base: `https://api.x.com`.
- Legacy host can set `TWITTER_API_BASE_URL=https://api.twitter.com`.

### Diagnostics API

File: `src/johny_twitter_branch/diagnostics.py`.

Classes/functions:

- `Check(name, ok, detail)` — one diagnostic result.
- `parse_env_file(path)` — simple dotenv parser.
- `secret_status(values)` — returns checks for required secrets with only `SET`/`MISSING`.
- `inspect_target(target)` — checks host runtime files, patch markers, `.env.example`, `.env`.
- `all_required_ok(checks)`.
- `format_checks(checks)`.

Marker expectations:

- `src/config.py` contains all `TWITTER_*` and `TOPIC_TWITTER`.
- `src/bot/router.py` contains `TWITTER = "twitter"`.
- `src/bot/helpers.py` contains `"twitter"`.
- `src/bot/setup.py` contains `"twitter": "Twitter"`.
- `src/bot/keyboards.py` contains `build_twitter_publish_keyboard` and `twitter_publish`.
- `src/main.py` contains `handle_twitter`, `handle_twitter_publish`, `twitter_publisher`, `twitter_publish`, `TOPIC_TWITTER`.
- `.env.example` contains Twitter fields.

### CLI contract

File: `src/johny_twitter_branch/cli.py`.

Commands:

```bash
python -m johny_twitter_branch guide
python -m johny_twitter_branch doctor --target /path/to/project
python -m johny_twitter_branch smoke-auth --env /path/to/project/.env
```

Equivalent before editable install:

```bash
PYTHONPATH=src python3 -m johny_twitter_branch guide
PYTHONPATH=src python3 -m johny_twitter_branch doctor --target /path/to/project
PYTHONPATH=src python3 -m johny_twitter_branch smoke-auth --env /path/to/project/.env
```

Behavior:

- `guide` prints agent/user checklist.
- `doctor` exits `0` when all checks pass, `1` when required markers/files are missing.
- `smoke-auth`:
  - reads `.env`;
  - prints only `SET`/`MISSING`;
  - returns `TWITTER_AUTH_OK=True` plus `USERNAME=@...` or `USER_ID=...` on success;
  - does not publish.

### Prompt contract

File: `prompts/twitter_post.md`.

Rules:

- Input text is source material, not a question to answer.
- Output exactly one ready Twitter/X post.
- Output language is always English.
- Russian/other source material is translated into natural English.
- Max length: 280 characters.
- No title, footer, explanation, assistant meta text, HTML or Markdown.
- No hashtags, emoji, CTA by default.
- No profit guarantees, insider promises or personal financial advice.
- For entry/buy/sell/market questions, convert to audience question or market observation instead of refusal/disclaimer.
- Do not publish personal data, private tokens, keys or seed phrases.
- Preserve links only when present and important.

### Host integration template behavior

File: `integration/johny_bot_clean/src/bot/twitter.py`.

Functions:

- `handle_twitter(update, context)`:
  - reads `message.text` or `message.caption`;
  - checks `message.message_thread_id == TOPIC_TWITTER`;
  - sends wait message `Готовлю твит...`;
  - gets text client for topic `twitter`;
  - builds generator via `context.bot_data["post_generator_factory"]` or `PostGenerator`;
  - calls `generate_post(source_text, prompt_name="twitter_post", style_prompt_name="danferat_stylev2")`;
  - hard-truncates to 280 if generator exceeds limit;
  - edits wait message with draft and `build_twitter_publish_keyboard(context)`;
  - stores draft via `create_post(... topic_type="twitter" ...)`;
  - on exception logs and edits wait message to error text.
- `handle_twitter_publish(update, context)`:
  - requires callback query and message;
  - checks admin + group authorization;
  - finds draft by bot message id;
  - blocks if draft missing;
  - blocks if already `published`;
  - uses latest revision if available, else generated text;
  - calls `context.bot_data["twitter_publisher"].publish(tweet_text)`;
  - marks post status `published`;
  - edits Telegram message with text and public URL.

Safety:

- No automatic publishing in `handle_twitter`.
- Publication only via callback `twitter_publish`.
- Missing credentials become callback alert, not a crash.

### Required host patch summary

In `src/config.py`:

- Add fields:
  - `TWITTER_API_KEY: str = ""`;
  - `TWITTER_API_SECRET: str = ""`;
  - `TWITTER_ACCESS_TOKEN: str = ""`;
  - `TWITTER_ACCESS_TOKEN_SECRET: str = ""`;
  - `TWITTER_API_BASE_URL: str = "https://api.x.com"`;
  - `TOPIC_TWITTER: int = 0`.
- Load those fields from env.

In `src/bot/router.py`:

- Add `TopicType.TWITTER = "twitter"`.

In `src/bot/helpers.py`:

- Add `"twitter"` to `TOPIC_TYPES`.

In `src/bot/setup.py`:

- Add `"twitter": "Twitter"` to `TOPIC_LABELS`.
- Add `/set_topic twitter` help text.

In `src/bot/keyboards.py`:

- Add `build_twitter_publish_keyboard(context)` with:
  - button `Опубликовать в Twitter`, callback `twitter_publish`;
  - model selector callback `writer_menu:twitter`.

In `src/main.py`:

- Import `handle_twitter`, `handle_twitter_publish`, `TwitterPublisher`.
- Initialize `application.bot_data["twitter_publisher"]`.
- Resolve `topic_twitter = overrides.get("TOPIC_TWITTER", config.TOPIC_TWITTER)`.
- Route matching text/caption to `handle_twitter`.
- Register `CallbackQueryHandler(handle_twitter_publish, pattern="^twitter_publish$")`.

Optional model defaults:

- `data/writer_models.json`: `"twitter": "anthropic"`.
- `data/claude_models.json`: `"twitter": "haiku"`.

### User installation flow

Simple user actions:

1. Clone module:

```bash
cd /root/Projects/Разработка
git clone https://github.com/Danferat/johny-twitter-branch-module.git
```

2. Ask an AI agent:

```text
Подключи модуль /root/Projects/Разработка/johny-twitter-branch-module
к моему проекту /path/to/johny-bot-clean-like-project.
Следуй AGENTS.md и docs/AGENT_PLAYBOOK_RU.md.
```

3. Get X API credentials at `https://console.x.com/`.
4. Enable Read and Write permissions.
5. Generate:
   - API Key;
   - API Secret;
   - Access Token;
   - Access Token Secret.
6. Put secrets into target `.env`.
7. In Telegram:
   - run `/setup_topics`; or
   - enter existing `Twitter` topic and run `/set_topic twitter`.
8. Send source text to `Twitter` topic.
9. Review draft.
10. Click `Опубликовать в Twitter`.

### Official X docs used

Checked on 2026-06-05:

- Getting access: `https://docs.x.com/x-api/getting-started/getting-access`.
- Developer Console: `https://docs.x.com/resources/fundamentals/developer-portal`.
- Create Post endpoint: `https://docs.x.com/x-api/posts/create-post`.
- Manage Posts quickstart: `https://docs.x.com/x-api/posts/manage-tweets/quickstart`.
- OAuth 1.0a API Key and Secret: `https://docs.x.com/fundamentals/authentication/oauth-1-0a/api-key-and-secret`.

### Verification already performed

In module:

```bash
python3 -m compileall -q src tests
```

Result: passed.

Using source project venv:

```bash
/root/Projects/Разработка/johny-bot-clean/.venv/bin/python -m compileall -q src tests integration
/root/Projects/Разработка/johny-bot-clean/.venv/bin/python -m pytest -q
```

Result:

- compileall passed;
- pytest: `8 passed`.

CLI checks:

```bash
PYTHONPATH=src python3 -m johny_twitter_branch guide
PYTHONPATH=src python3 -m johny_twitter_branch doctor --target /root/Projects/Разработка/johny-bot-clean
PYTHONPATH=src python3 -m johny_twitter_branch smoke-auth --env .env.example
```

Results:

- `guide` passed;
- `doctor` on `/root/Projects/Разработка/johny-bot-clean` showed all checks OK;
- `smoke-auth --env .env.example` showed expected `MISSING` and did not publish.

GitHub publication:

```bash
git init -b main
git add .
git commit -m "Create Twitter branch module"
gh repo create johny-twitter-branch-module --public --source . --remote origin --push
git ls-remote --heads origin main
```

Result:

- repo created: `https://github.com/Danferat/johny-twitter-branch-module`;
- branch `main` pushed;
- remote branch confirmed: `5734cb2292a685532e983787427ce1553eb1d94f refs/heads/main`.

### Current status

- Local working tree was clean before this сжимание.
- This update changes `CHANGELOG.md` only.
- Runtime code is unchanged by this сжимание.
- GitHub copy should contain this System State after the next documentation commit is pushed.

### Open tasks

- Optional: add GitHub release/tag `v0.1.0`.
- Optional: add CI workflow for `compileall` and pytest.
- Optional: add packaging metadata for PyPI if public package distribution becomes necessary.
