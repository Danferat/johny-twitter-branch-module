## 2026-06-08 10:49 UTC
- Контекст: Нужно перенести в переносимый Twitter/X branch module новое правило host-проекта: X API не вызывается при генерации/правках/выборе модели, а только по явной кнопке публикации.
- Изменение: Интеграционный handler теперь требует `mark_post_publishing()` перед `TwitterPublisher.publish()`; диагностика `doctor` проверяет marker `src/db/models.py`; docs/README/CLI/playbook описывают обязательный сценарий `draft -> publishing -> published` и запрет X API до `twitter_publish`.
- Затронуто: `README.md`, `src/johny_twitter_branch/constants.py`, `src/johny_twitter_branch/diagnostics.py`, `src/johny_twitter_branch/cli.py`, `integration/johny_bot_clean/src/bot/twitter.py`, `integration/johny_bot_clean/tests/test_twitter.py`, `docs/AGENT_PLAYBOOK_RU.md`, `docs/DEBUGGING_RU.md`, `docs/INTEGRATION_PATCHES_RU.md`, `docs/USER_SETUP_RU.md`, `tests/test_diagnostics.py`.
- Эффект: Новые подключения модуля получают idempotency guard: повторный callback/двойной клик не должен доходить до X publisher, а любые действия с черновиком до publish-кнопки остаются без Twitter/X API.
- Проверка: `/root/Projects/Разработка/johny-bot-clean/.venv/bin/python -m compileall -q src tests integration` -> passed; `PYTHONPATH=src /root/Projects/Разработка/johny-bot-clean/.venv/bin/python -m pytest -q tests` -> `9 passed`; `PYTHONPATH=src /root/Projects/Разработка/johny-bot-clean/.venv/bin/python -m johny_twitter_branch doctor --target /root/Projects/Разработка/johny-bot-clean` -> all checks OK, including `src/db/models.py`.
- CHANGELOG: нет

## 2026-06-05 16:13 UTC
- Контекст: Нужно выделить сегодняшнюю Twitter-ветку из `/root/Projects/Разработка/johny-bot-clean` в отдельный модуль, готовый к публикации на GitHub и подключению агентом к похожему проекту.
- Изменение: Создан отдельный проект `johny-twitter-branch-module` с переносимым publisher, CLI guide/doctor/smoke-auth, prompt, integration templates и инструкциями для агента/пользователя.
- Затронуто: `README.md`, `AGENTS.md`, `src/johny_twitter_branch/*`, `prompts/twitter_post.md`, `integration/johny_bot_clean/*`, `docs/*`, tests.
- Эффект: Модуль можно клонировать, проверить и подключить к аналогу `johny-bot-clean` без переноса локальных секретов и без ручного ввода numeric Telegram user/group IDs как основного способа настройки.
- Проверка: `python3 -m compileall -q src tests` -> passed; `/root/Projects/Разработка/johny-bot-clean/.venv/bin/python -m compileall -q src tests integration` -> passed; `/root/Projects/Разработка/johny-bot-clean/.venv/bin/python -m pytest -q` -> `8 passed`; `PYTHONPATH=src python3 -m johny_twitter_branch guide` -> passed; `PYTHONPATH=src python3 -m johny_twitter_branch doctor --target /root/Projects/Разработка/johny-bot-clean` -> all checks OK; `PYTHONPATH=src python3 -m johny_twitter_branch smoke-auth --env .env.example` -> expected MISSING without publishing.
- CHANGELOG: да
