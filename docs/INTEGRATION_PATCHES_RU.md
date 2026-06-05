# Точки подключения в johny-bot-clean-like проекте

Файлы из `integration/johny_bot_clean/` рассчитаны на проект с архитектурой, близкой к `/root/Projects/Разработка/johny-bot-clean`. Если host отличается, не копируй слепо: сохрани смысл контрактов.

## 1. Скопировать runtime

```bash
cp integration/johny_bot_clean/src/bot/twitter.py /path/to/target/src/bot/twitter.py
cp integration/johny_bot_clean/src/services/twitter_publisher.py /path/to/target/src/services/twitter_publisher.py
cp prompts/twitter_post.md /path/to/target/src/prompts/twitter_post.md
```

## 2. `.env.example` и `.env`

Добавить:

```env
TWITTER_API_KEY=
TWITTER_API_SECRET=
TWITTER_ACCESS_TOKEN=
TWITTER_ACCESS_TOKEN_SECRET=
TWITTER_API_BASE_URL=https://api.x.com
TOPIC_TWITTER=0
```

В реальном `.env` `TOPIC_TWITTER` можно оставить `0`, если проект использует `/setup_topics` или `/set_topic twitter` и хранит overrides в `data/topics.json`.

## 3. `src/config.py`

В `Config` добавить:

```python
TWITTER_API_KEY: str = ""
TWITTER_API_SECRET: str = ""
TWITTER_ACCESS_TOKEN: str = ""
TWITTER_ACCESS_TOKEN_SECRET: str = ""
TWITTER_API_BASE_URL: str = "https://api.x.com"
TOPIC_TWITTER: int = 0
```

В `load_config()` добавить:

```python
TWITTER_API_KEY=os.environ.get("TWITTER_API_KEY", "").strip(),
TWITTER_API_SECRET=os.environ.get("TWITTER_API_SECRET", "").strip(),
TWITTER_ACCESS_TOKEN=os.environ.get("TWITTER_ACCESS_TOKEN", "").strip(),
TWITTER_ACCESS_TOKEN_SECRET=os.environ.get(
    "TWITTER_ACCESS_TOKEN_SECRET", ""
).strip(),
TWITTER_API_BASE_URL=os.environ.get(
    "TWITTER_API_BASE_URL", "https://api.x.com"
).strip(),
TOPIC_TWITTER=_env_int("TOPIC_TWITTER"),
```

## 4. `src/bot/router.py`

В enum semantic topics добавить:

```python
TWITTER = "twitter"
```

## 5. `src/bot/helpers.py`

В `TOPIC_TYPES` добавить:

```python
"twitter",
```

Это нужно для `/writer`, model selection и определения текущего topic.

## 6. `src/bot/setup.py`

В `TOPIC_LABELS` добавить:

```python
"twitter": "Twitter",
```

В help text для `/set_topic` добавить строку:

```text
  twitter — Twitter/X (черновик и публикация через API)
```

Важно: если `data/topics.json` уже есть, не добавляй туда `"twitter": 0`. Нулевой persisted override может перекрыть `TOPIC_TWITTER` из `.env`.

## 7. `src/bot/keyboards.py`

Добавить клавиатуру:

```python
def build_twitter_publish_keyboard(
    context: ContextTypes.DEFAULT_TYPE,
) -> InlineKeyboardMarkup:
    writer_label = get_writer_display_label(context, "twitter")
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Опубликовать в Twitter",
                    callback_data="twitter_publish",
                )
            ],
            [
                InlineKeyboardButton(
                    f"Модель: {writer_label}",
                    callback_data="writer_menu:twitter",
                )
            ],
        ]
    )
```

## 8. `src/main.py`

Импорты:

```python
from src.bot.twitter import handle_twitter, handle_twitter_publish
from src.services.twitter_publisher import TwitterPublisher
```

В `post_init()`:

```python
application.bot_data["twitter_publisher"] = TwitterPublisher(
    api_key=config.TWITTER_API_KEY,
    api_secret=config.TWITTER_API_SECRET,
    access_token=config.TWITTER_ACCESS_TOKEN,
    access_token_secret=config.TWITTER_ACCESS_TOKEN_SECRET,
    api_base_url=getattr(config, "TWITTER_API_BASE_URL", "https://api.x.com"),
)
```

В text router добавить effective topic:

```python
topic_twitter = overrides.get("TOPIC_TWITTER", config.TOPIC_TWITTER)
```

И route до fallback/new_post:

```python
if thread_id == topic_twitter and topic_twitter != 0:
    await handle_twitter(update, context)
    return
```

В callback handlers:

```python
application.add_handler(
    CallbackQueryHandler(handle_twitter_publish, pattern="^twitter_publish$")
)
```

## 9. Model defaults

Если проект использует per-topic model JSON, добавить:

`data/writer_models.json`:

```json
{
  "twitter": "anthropic"
}
```

`data/claude_models.json`:

```json
{
  "twitter": "haiku"
}
```

Сохрани существующие ключи; не перезаписывай весь JSON ради одного topic.

## 10. Тесты

Скопировать:

```bash
cp integration/johny_bot_clean/tests/test_twitter.py /path/to/target/tests/test_twitter.py
```

Адаптировать только если host storage/router отличается.

Минимальная проверка:

```bash
python -m compileall -q src tests
python -m pytest -q tests/test_twitter.py tests/test_config.py tests/test_router.py
python -m johny_twitter_branch doctor --target /path/to/target
```

