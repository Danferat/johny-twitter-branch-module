# Где взять Twitter/X API credentials

Документы X меняются, поэтому перед установкой проверьте актуальные страницы:

- Getting access: https://docs.x.com/x-api/getting-started/getting-access
- Developer Console: https://docs.x.com/resources/fundamentals/developer-portal
- Create Post endpoint: https://docs.x.com/x-api/posts/create-post
- Manage Posts quickstart: https://docs.x.com/x-api/posts/manage-tweets/quickstart
- OAuth 1.0a API Key and Secret: https://docs.x.com/fundamentals/authentication/oauth-1-0a/api-key-and-secret

Проверено: 2026-06-05.

## Какие credentials нужны

Для этого модуля нужны OAuth 1.0a user-context credentials:

- `TWITTER_API_KEY`
- `TWITTER_API_SECRET`
- `TWITTER_ACCESS_TOKEN`
- `TWITTER_ACCESS_TOKEN_SECRET`

Bearer Token сам по себе подходит для некоторых read-only запросов, но не является заменой для публикации от имени аккаунта в этом модуле.

## Пошагово

1. Зайдите в `https://console.x.com/`.
2. Создайте или выберите Project/App.
3. В настройках App включите права, позволяющие писать posts. Обычно это режим Read and Write.
4. Откройте раздел keys/tokens.
5. Скопируйте API Key и API Secret.
6. Сгенерируйте Access Token и Access Token Secret для аккаунта, от имени которого будут публиковаться посты.
7. Сохраните значения сразу: X может показать секреты только один раз.
8. Запишите их в `.env` целевого проекта:

```env
TWITTER_API_KEY=...
TWITTER_API_SECRET=...
TWITTER_ACCESS_TOKEN=...
TWITTER_ACCESS_TOKEN_SECRET=...
TWITTER_API_BASE_URL=https://api.x.com
```

## Безопасность

- Не отправляйте секреты в чат с агентом, если можно положить их напрямую в `.env`.
- Не коммитьте `.env`.
- Если секрет попал в лог или git, сразу regenerate/rotate credentials в X Developer Console.
- Давайте приложению минимально нужные права.

