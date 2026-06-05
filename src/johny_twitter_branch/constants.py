"""Stable integration constants for the Twitter/X branch."""

TOPIC_TYPE = "twitter"
TOPIC_LABEL = "Twitter"
PROMPT_NAME = "twitter_post"
CALLBACK_DATA = "twitter_publish"

ENV_FIELDS = (
    "TWITTER_API_KEY",
    "TWITTER_API_SECRET",
    "TWITTER_ACCESS_TOKEN",
    "TWITTER_ACCESS_TOKEN_SECRET",
    "TWITTER_API_BASE_URL",
    "TOPIC_TWITTER",
)

REQUIRED_SECRET_FIELDS = (
    "TWITTER_API_KEY",
    "TWITTER_API_SECRET",
    "TWITTER_ACCESS_TOKEN",
    "TWITTER_ACCESS_TOKEN_SECRET",
)

HOST_RUNTIME_FILES = (
    "src/bot/twitter.py",
    "src/services/twitter_publisher.py",
    "src/prompts/twitter_post.md",
)

HOST_PATCH_POINTS = (
    "src/config.py",
    "src/bot/router.py",
    "src/bot/helpers.py",
    "src/bot/setup.py",
    "src/bot/keyboards.py",
    "src/main.py",
    ".env.example",
)

