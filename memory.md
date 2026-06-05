## 2026-06-05 16:13 UTC
- Контекст: Нужно выделить сегодняшнюю Twitter-ветку из `/root/Projects/Разработка/johny-bot-clean` в отдельный модуль, готовый к публикации на GitHub и подключению агентом к похожему проекту.
- Изменение: Создан отдельный проект `johny-twitter-branch-module` с переносимым publisher, CLI guide/doctor/smoke-auth, prompt, integration templates и инструкциями для агента/пользователя.
- Затронуто: `README.md`, `AGENTS.md`, `src/johny_twitter_branch/*`, `prompts/twitter_post.md`, `integration/johny_bot_clean/*`, `docs/*`, tests.
- Эффект: Модуль можно клонировать, проверить и подключить к аналогу `johny-bot-clean` без переноса локальных секретов и без ручного ввода numeric Telegram user/group IDs как основного способа настройки.
- Проверка: `python3 -m compileall -q src tests` -> passed; `/root/Projects/Разработка/johny-bot-clean/.venv/bin/python -m compileall -q src tests integration` -> passed; `/root/Projects/Разработка/johny-bot-clean/.venv/bin/python -m pytest -q` -> `8 passed`; `PYTHONPATH=src python3 -m johny_twitter_branch guide` -> passed; `PYTHONPATH=src python3 -m johny_twitter_branch doctor --target /root/Projects/Разработка/johny-bot-clean` -> all checks OK; `PYTHONPATH=src python3 -m johny_twitter_branch smoke-auth --env .env.example` -> expected MISSING without publishing.
- CHANGELOG: да
