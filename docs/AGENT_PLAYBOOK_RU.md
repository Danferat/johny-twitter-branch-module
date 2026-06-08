# Playbook для агента

## Цель

Подключить ветку `Twitter` в похожий Telegram content-bot проект без лишней архитектуры и без утечки секретов.

## Допущения

- В проекте уже есть Telegram forum topics.
- Есть генератор текста, совместимый с `PostGenerator.generate_post`.
- Есть таблица/хранилище черновиков, где пост можно найти по `bot_message_id`.
- Есть inline callback routing.
- Публикация должна быть ручной: входящее сообщение создаёт только черновик.

Если одно из допущений неверно, не ломай проект под шаблон. Используй publisher и prompt как ядро, а handler адаптируй под местную архитектуру.

## План: шаг -> проверка

1. Изучи host project:
   - проверка: найдены `src/main.py`, `src/config.py`, Telegram handlers, prompt loader, post storage.
2. Скопируй runtime-файлы:
   - проверка: есть `src/bot/twitter.py`, `src/services/twitter_publisher.py`, `src/prompts/twitter_post.md`.
3. Добавь config/env поля:
   - проверка: `TOPIC_TWITTER` и четыре `TWITTER_*` читаются из `.env`.
4. Добавь semantic topic `twitter`:
   - проверка: `/set_topic twitter`, `/setup_topics`, model selection и topic resolver видят `twitter`.
5. Подключи router/main:
   - проверка: текст в `TOPIC_TWITTER` вызывает `handle_twitter`, callback `twitter_publish` вызывает `handle_twitter_publish`.
6. Подключи кнопку публикации:
   - проверка: черновик содержит inline button `Опубликовать в Twitter`.
7. Подключи idempotency guard:
   - проверка: `src/db/models.py` содержит `mark_post_publishing`; publish handler делает `draft -> publishing` до X API и повторный callback не вызывает publisher.
8. Прогони тесты:
   - проверка: compileall и targeted pytest проходят.
9. Попроси пользователя заполнить API:
   - проверка: `smoke-auth` показывает только `SET/MISSING`, `TWITTER_AUTH_OK=True` и `USERNAME=@...`.
10. Проведи end-to-end в Telegram:
   - проверка: draft создаётся, публикация требует нажатия, сообщение обновляется ссылкой на пост.

## Что нельзя делать

- Не публиковать автоматически при получении текста.
- Не вызывать Twitter/X API при генерации, рерайте, выборе формата или выборе модели; внешний X POST разрешён только в `twitter_publish` после явного нажатия кнопки.
- Не вызывать `TwitterPublisher.publish()` без атомарного `draft -> publishing` lock.
- Не выводить секреты в терминал, README, логи, тесты, final report.
- Не использовать Bearer Token как замену user-context credentials для публикации.
- Не просить numeric Telegram user/channel IDs как основной формат пользовательской настройки. Используй `@username` или `https://t.me/...`, а topic id пусть ловят команды.
- Не записывать `twitter: 0` в persisted topic overrides, если это перекрывает `.env`.

## Команды

```bash
python -m johny_twitter_branch guide
python -m johny_twitter_branch doctor --target /path/to/target
python -m compileall -q src tests
python -m pytest -q tests/test_twitter.py tests/test_config.py tests/test_router.py
python -m johny_twitter_branch smoke-auth --env /path/to/target/.env
```
