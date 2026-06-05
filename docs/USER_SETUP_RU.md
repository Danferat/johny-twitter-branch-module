# Инструкция для пользователя

## Что делает модуль

Модуль добавляет в Telegram-бота отдельную ветку `Twitter`.

Вы отправляете туда идею, пост, пересланный текст или caption. Бот делает короткий англоязычный черновик для Twitter/X. Публикация происходит только после нажатия кнопки `Опубликовать в Twitter`.

## Что подготовить

- Доступ к группе Telegram, где работает бот.
- Права администратора в боте.
- X developer account.
- X app с правом публиковать posts.
- Четыре секрета для `.env`:
  - `TWITTER_API_KEY`
  - `TWITTER_API_SECRET`
  - `TWITTER_ACCESS_TOKEN`
  - `TWITTER_ACCESS_TOKEN_SECRET`

## Настройка Telegram

1. Откройте группу, где работает бот.
2. Убедитесь, что включены forum topics.
3. Запустите `/setup_topics`, если проект поддерживает автосоздание веток.
4. Если ветка уже есть, зайдите в неё и отправьте `/set_topic twitter`.
5. Не нужно вручную искать numeric Telegram user/group ID. Для пользователей и групп в инструкциях используйте `@username` или `https://t.me/...`.

## Настройка X API

См. [X_API_KEYS_RU.md](X_API_KEYS_RU.md).

Коротко:

1. Откройте `https://console.x.com/`.
2. Создайте developer app.
3. Включите права Read and Write.
4. Сгенерируйте API Key/Secret и Access Token/Secret.
5. Передайте значения только через `.env` или secret manager.

## Проверка

Попросите агента выполнить:

```bash
python -m johny_twitter_branch doctor --target /path/to/project
python -m johny_twitter_branch smoke-auth --env /path/to/project/.env
```

Нормальный результат smoke-test:

```text
TWITTER_AUTH_OK=True
USERNAME=@your_account
```

## Работа

1. Отправьте исходный текст в ветку `Twitter`.
2. Дождитесь черновика.
3. Если нужно, ответьте на сообщение бота правкой.
4. Когда текст готов, нажмите `Опубликовать в Twitter`.

