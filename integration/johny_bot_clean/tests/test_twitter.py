from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.bot.twitter import handle_twitter, handle_twitter_publish
from src.services.twitter_publisher import TwitterPublishError, TwitterPublisher


TOPIC_TWITTER_ID = 44


def _make_context(*, generator: AsyncMock | None = None) -> MagicMock:
    context = MagicMock()
    context.bot_data = {
        "config": MagicMock(
            DB_PATH=":memory:",
            TOPIC_TWITTER=TOPIC_TWITTER_ID,
            ADMIN_TELEGRAM_ID=42,
            GROUP_ID=100,
            CLAUDE_CLI_MODEL="sonnet",
            DEFAULT_TEXT_PROVIDER="anthropic",
        ),
        "topic_overrides": {},
        "text_ai_clients": {"anthropic": AsyncMock()},
    }
    if generator is not None:
        context.bot_data["post_generator_factory"] = MagicMock(
            return_value=generator
        )
    return context


def _make_text_update() -> MagicMock:
    update = MagicMock()
    message = MagicMock()
    message.text = "идея из экосистемы проекта"
    message.caption = None
    message.chat_id = 100
    message.message_thread_id = TOPIC_TWITTER_ID
    wait_msg = AsyncMock()
    wait_msg.message_id = 777
    wait_msg.edit_text = AsyncMock(return_value=SimpleNamespace(message_id=777))
    message.reply_text = AsyncMock(return_value=wait_msg)
    update.effective_message = message
    return update


@pytest.mark.asyncio
async def test_handle_twitter_generates_draft_with_twitter_prompt() -> None:
    generator = AsyncMock()
    generator.generate_post = AsyncMock(return_value="Short tweet")
    context = _make_context(generator=generator)
    update = _make_text_update()

    with patch("src.bot.twitter.get_db") as mock_get_db:
        db = AsyncMock()
        mock_get_db.return_value = db
        with patch("src.bot.twitter.create_post", new=AsyncMock()) as mock_create:
            await handle_twitter(update, context)

    generator.generate_post.assert_awaited_once_with(
        "идея из экосистемы проекта",
        prompt_name="twitter_post",
        style_prompt_name="danferat_stylev2",
    )
    update.effective_message.reply_text.assert_awaited_once()
    mock_create.assert_awaited_once()
    assert mock_create.await_args.kwargs["topic_type"] == "twitter"


@pytest.mark.asyncio
async def test_handle_twitter_publish_surfaces_missing_credentials() -> None:
    update = MagicMock()
    message = MagicMock()
    message.message_id = 777
    message.chat_id = 100
    message.chat = MagicMock()
    query = AsyncMock()
    query.message = message
    query.from_user = SimpleNamespace(id=42)
    query.answer = AsyncMock()
    update.callback_query = query

    context = _make_context()
    context.bot_data["twitter_publisher"] = TwitterPublisher()

    post = {
        "id": 1,
        "status": "draft",
        "generated_text": "Short tweet",
    }

    with patch("src.bot.twitter.get_db") as mock_get_db:
        db = AsyncMock()
        mock_get_db.return_value = db
        with patch(
            "src.bot.twitter.get_post_by_message_id",
            AsyncMock(return_value=post),
        ):
            with patch(
                "src.bot.twitter.get_latest_revision_for_post",
                AsyncMock(return_value=None),
            ):
                with patch(
                    "src.bot.twitter.mark_post_publishing",
                    AsyncMock(return_value=True),
                ):
                    with patch("src.bot.twitter.update_post_status", AsyncMock()):
                        await handle_twitter_publish(update, context)

    assert query.answer.await_args_list[-1].kwargs["show_alert"] is True


@pytest.mark.asyncio
async def test_handle_twitter_publish_skips_when_publish_already_in_progress() -> None:
    update = MagicMock()
    message = MagicMock()
    message.message_id = 777
    message.chat_id = 100
    message.chat = MagicMock()
    query = AsyncMock()
    query.message = message
    query.from_user = SimpleNamespace(id=42)
    query.answer = AsyncMock()
    update.callback_query = query

    context = _make_context()
    publisher = AsyncMock()
    publisher.publish = AsyncMock()
    context.bot_data["twitter_publisher"] = publisher

    post = {
        "id": 1,
        "status": "draft",
        "generated_text": "Short tweet",
    }

    with patch("src.bot.twitter.get_db") as mock_get_db:
        db = AsyncMock()
        mock_get_db.return_value = db
        with patch(
            "src.bot.twitter.get_post_by_message_id",
            AsyncMock(return_value=post),
        ):
            with patch(
                "src.bot.twitter.get_latest_revision_for_post",
                AsyncMock(return_value=None),
            ):
                with patch(
                    "src.bot.twitter.mark_post_publishing",
                    AsyncMock(return_value=False),
                ):
                    await handle_twitter_publish(update, context)

    publisher.publish.assert_not_awaited()
    query.answer.assert_awaited_once_with(
        "Публикация уже запущена или завершена.",
        show_alert=True,
    )


def test_twitter_publisher_requires_credentials() -> None:
    publisher = TwitterPublisher()
    assert publisher.is_configured is False

    with pytest.raises(TwitterPublishError, match="Twitter"):
        asyncio.run(publisher.publish("hello"))
