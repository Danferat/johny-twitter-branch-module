"""Handler for the Twitter/X topic in a johny-bot-clean-like host."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from src.bot.helpers import (
    get_text_client_for_topic,
    get_topic_id,
    is_authorized_admin_user,
    is_authorized_group_chat,
)
from src.bot.keyboards import build_twitter_publish_keyboard
from src.config import get_config
from src.db.database import get_db
from src.db.models import (
    create_post,
    get_latest_revision_for_post,
    get_post_by_message_id,
    update_post_status,
)
from src.services.post_generator import PostGenerator
from src.services.twitter_publisher import TwitterPublishError, TwitterPublisher

logger = logging.getLogger(__name__)


async def handle_twitter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate a Twitter/X-ready draft from text in the Twitter topic."""
    message = update.effective_message
    if not message:
        return

    source_text = message.text or message.caption
    if not source_text:
        return

    expected_topic = get_topic_id(context, "TOPIC_TWITTER")
    if message.message_thread_id != expected_topic:
        return

    wait_msg = await message.reply_text(
        "Готовлю твит...",
        message_thread_id=message.message_thread_id,
    )

    config = context.bot_data.get("config") or get_config()
    try:
        text_client = get_text_client_for_topic(context, "twitter")
        generator: PostGenerator = (
            context.bot_data.get("post_generator_factory", PostGenerator)
        )(text_client)
        tweet_text = await generator.generate_post(
            source_text,
            prompt_name="twitter_post",
            style_prompt_name="danferat_stylev2",
        )

        if len(tweet_text) > 280:
            tweet_text = tweet_text[:277].rstrip() + "..."

        bot_msg = await wait_msg.edit_text(
            tweet_text,
            reply_markup=build_twitter_publish_keyboard(context),
        )

        db = await get_db(config.DB_PATH)
        try:
            await create_post(
                db=db,
                topic_type="twitter",
                original_text=source_text,
                generated_text=tweet_text,
                chat_id=message.chat_id,
                topic_id=message.message_thread_id or 0,
                bot_message_id=bot_msg.message_id,
            )
        finally:
            await db.close()

    except Exception as exc:
        logger.error("Error generating tweet draft: %s", exc)
        await wait_msg.edit_text("Ошибка при генерации твита. Попробуй ещё раз.")


async def handle_twitter_publish(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Publish the generated Post attached to the clicked button."""
    query = update.callback_query
    if query is None or query.message is None:
        return

    config = context.bot_data.get("config") or get_config()
    if not (
        is_authorized_admin_user(query.from_user, config)
        and is_authorized_group_chat(query.message.chat, query.message.chat_id, config)
    ):
        await query.answer()
        return

    db = await get_db(config.DB_PATH)
    try:
        post = await get_post_by_message_id(db, query.message.message_id)
        if post is None:
            await query.answer(
                "Не нашёл черновик твита. Пришли текст ещё раз.",
                show_alert=True,
            )
            return

        if post["status"] == "published":
            await query.answer("Уже опубликовано", show_alert=True)
            return

        revision = await get_latest_revision_for_post(db, post["id"])
        tweet_text = (
            revision["revised_text"]
            if revision is not None
            else post["generated_text"]
        )

        publisher: TwitterPublisher = context.bot_data.get(
            "twitter_publisher",
            TwitterPublisher(),
        )
        result = await publisher.publish(tweet_text)
        await update_post_status(
            db,
            post["id"],
            status="published",
            ready_message_id=None,
            ready_topic_id=None,
        )
    except TwitterPublishError as exc:
        await query.answer(str(exc), show_alert=True)
        return
    finally:
        await db.close()

    await query.answer("Опубликовано")
    await query.edit_message_text(
        f"{tweet_text}\n\nОпубликовано: {result.url}",
        disable_web_page_preview=True,
    )

