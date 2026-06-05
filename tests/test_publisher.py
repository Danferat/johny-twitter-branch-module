from __future__ import annotations

import asyncio

import pytest

from johny_twitter_branch.publisher import (
    TwitterPublishError,
    TwitterPublishResult,
    TwitterPublisher,
)


def test_publish_requires_credentials_before_network() -> None:
    publisher = TwitterPublisher()

    with pytest.raises(TwitterPublishError, match="not configured"):
        asyncio.run(publisher.publish("hello"))


def test_publish_rejects_empty_text() -> None:
    publisher = TwitterPublisher(
        api_key="key",
        api_secret="secret",
        access_token="token",
        access_token_secret="token-secret",
    )

    with pytest.raises(TwitterPublishError, match="empty"):
        asyncio.run(publisher.publish("   "))


def test_publish_rejects_oversized_text() -> None:
    publisher = TwitterPublisher(
        api_key="key",
        api_secret="secret",
        access_token="token",
        access_token_secret="token-secret",
    )

    with pytest.raises(TwitterPublishError, match="280"):
        asyncio.run(publisher.publish("x" * 281))


def test_result_url_uses_public_base() -> None:
    result = TwitterPublishResult(post_id="123", text="hello")

    assert result.tweet_id == "123"
    assert result.url == "https://x.com/i/web/status/123"


def test_from_env_accepts_mapping() -> None:
    publisher = TwitterPublisher.from_env(
        {
            "TWITTER_API_KEY": " key ",
            "TWITTER_API_SECRET": " secret ",
            "TWITTER_ACCESS_TOKEN": " token ",
            "TWITTER_ACCESS_TOKEN_SECRET": " token-secret ",
            "TWITTER_API_BASE_URL": "https://api.twitter.com/",
        }
    )

    assert publisher.is_configured is True
    assert publisher.api_base_url == "https://api.twitter.com"

