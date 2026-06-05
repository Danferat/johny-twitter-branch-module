# Отладка

## 1. Проверить, что модуль подключён

```bash
python -m johny_twitter_branch doctor --target /path/to/project
```

Если есть `MISS`, агент должен исправить конкретную точку:

- runtime-файлы: скопировать из `integration/johny_bot_clean/`;
- config/router/setup/main: сверить с `docs/INTEGRATION_PATCHES_RU.md`;
- `.env`: добавить недостающие поля.

## 2. Проверить Python

```bash
python -m compileall -q src tests
python -m pytest -q tests/test_twitter.py
```

Если в проекте есть старые подвисающие тесты, запускайте узкий набор по Twitter-ветке и явно зафиксируйте остаточный риск.

## 3. Проверить credentials без публикации

```bash
python -m johny_twitter_branch smoke-auth --env /path/to/project/.env
```

Ожидаемо:

```text
TWITTER_AUTH_OK=True
USERNAME=@...
```

Проблемы:

- `MISSING`: поле отсутствует или пустое в `.env`.
- `401/403`: проверьте app permissions, regenerated access token, правильный account.
- network error: проверьте DNS/egress/firewall.

## 4. Черновик есть, публикация не работает

Проверьте:

- inline callback `twitter_publish` зарегистрирован в `src/main.py`;
- `context.bot_data["twitter_publisher"]` инициализируется после загрузки config;
- App имеет права Read and Write;
- Access Token/Secret сгенерированы после включения Read and Write;
- текст не длиннее 280 символов.

## 5. Сообщение в ветке игнорируется

Проверьте:

- `TOPIC_TWITTER` не равен `0`;
- topic привязан через `/set_topic twitter` или создан через `/setup_topics`;
- в persisted `data/topics.json` нет `"twitter": 0`, если это перекрывает `.env`;
- router сравнивает `message.message_thread_id` с `TOPIC_TWITTER`.

## 6. Твит выглядит как ответ ассистента

Проверьте, что в target project лежит свежий `src/prompts/twitter_post.md`. Он должен явно говорить, что входящий текст - сырьё для публикации, а не вопрос к ассистенту.

