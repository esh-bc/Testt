# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   handlers/search.py — inline search + callbacks
#   © AnimeTadka
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import hashlib

from aiogram import Router, Bot, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineQuery, InlineQueryResultArticle,
    InputTextMessageContent,
)
from aiogram.enums import ChatType

from utils.api import search_anime, enrich_results
from utils.messages import (
    search_result_card,
    no_results_msg, DIV2
)
from utils.keyboards import (
    search_list_keyboard, detail_card_keyboard, no_results_keyboard
)
from utils import db
from config import CREDIT_LINE, PAGE_SIZE, AUTO_DELETE_DELAY

router = Router()

# In-memory cache: "{chat_id}:{user_id}" → list of enriched results
_search_cache: dict[str, list] = {}

# In-memory store of the last "no results" query per user per chat
# Used by the auto_req callback to know what to request
_no_result_query: dict[str, str] = {}


def _mention(user) -> str:
    if user.username:
        return f"@{user.username}"
    return f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"


def _cache_key(chat_id: int, user_id: int) -> str:
    return f"{chat_id}:{user_id}"


async def _schedule(
    bot_msg: Message,
    user_msg_id: int | None = None,
    delay: int = AUTO_DELETE_DELAY
):
    """Helper — schedule deletion of bot message (and optionally user message)."""
    try:
        await db.schedule_deletion(
            chat_id=bot_msg.chat.id,
            bot_message_id=bot_msg.message_id,
            user_message_id=user_msg_id,
            delay_seconds=delay
        )
    except Exception:
        pass


# ── Pagination callback ────────────────────────────

@router.callback_query(F.data.startswith("page:"))
async def handle_pagination(callback: CallbackQuery):
    parts    = callback.data.split(":", 2)
    page     = int(parts[1])
    query    = parts[2]

    key      = _cache_key(callback.message.chat.id, callback.from_user.id)
    enriched = _search_cache.get(key)

    if not enriched:
        await callback.answer("◈ mou~ session expired~ search again~", show_alert=True)
        return

    kb = search_list_keyboard(enriched, page=page, query=query)
    try:
        await callback.message.edit_reply_markup(reply_markup=kb)
    except Exception:
        pass
    await callback.answer()


# ── Select anime callback ──────────────────────────

@router.callback_query(F.data.startswith("select:"))
async def handle_select(callback: CallbackQuery, bot: Bot):
    parts = callback.data.split(":", 2)
    index = int(parts[1])

    key      = _cache_key(callback.message.chat.id, callback.from_user.id)
    enriched = _search_cache.get(key)

    if not enriched or index >= len(enriched):
        await callback.answer("◈ mou~ session expired~ search again~", show_alert=True)
        return

    result = enriched[index]
    card   = search_result_card(result)
    kb     = detail_card_keyboard(
        watch_url=result.get("watch_url", ""),
        mal_id=result.get("mal_id")
    )

    poster = result.get("poster")
    await callback.answer()

    # The user message that triggered the original /s is the reply_to of the list msg
    user_cmd_id = None
    if callback.message.reply_to_message:
        user_cmd_id = callback.message.reply_to_message.message_id

    if poster:
        try:
            sent = await callback.message.answer_photo(
                photo=poster,
                caption=card,
                parse_mode="HTML",
                reply_markup=kb
            )
            await _schedule(sent, user_cmd_id)
            return
        except Exception:
            pass

    sent = await callback.message.answer(card, parse_mode="HTML", reply_markup=kb)
    await _schedule(sent, user_cmd_id)


# ── Auto-request callback (no results → Request button) ──

@router.callback_query(F.data == "auto_req")
async def handle_auto_req(callback: CallbackQuery, bot: Bot):
    """
    Fires when user taps 'Request This Anime' on a no-results message.
    Automatically submits the request using the stored query — no typing needed.
    """
    key   = _cache_key(callback.message.chat.id, callback.from_user.id)
    query = _no_result_query.get(key)

    if not query:
        await callback.answer(
            "◈ mou~ session expired~ search again first~",
            show_alert=True
        )
        return

    user    = callback.from_user
    mention = (f"@{user.username}" if user.username
               else f"<a href='tg://user?id={user.id}'>{user.first_name}</a>")

    await db.add_request(
        user.id,
        user.username or "unknown",
        query,
        callback.message.chat.id,
        callback.message.chat.title or "Unknown"
    )

    # Edit the no-results message in place to confirm
    try:
        await callback.message.edit_text(
            f"✦ ara~ {mention} wants <b>{query}</b>~\n"
            f"◈ noted~ i'll haunt the owner until they add it~\n"
            f"◇ don't hold your breath though~\n"
            f"{DIV2}\n"
            f"<i>{CREDIT_LINE}</i>",
            parse_mode="HTML"
        )
    except Exception:
        pass

    await callback.answer("✦ request submitted~")

    # Clean up stored query
    _no_result_query.pop(key, None)


# ── noop callback (page indicator button) ─────────

@router.callback_query(F.data == "noop")
async def handle_noop(callback: CallbackQuery):
    await callback.answer()


# ── Close callback ─────────────────────────────────
# Deletes the bot message immediately AND the user's original command message

@router.callback_query(F.data == "close_result")
async def close_result(callback: CallbackQuery, bot: Bot):
    chat_id    = callback.message.chat.id
    bot_msg_id = callback.message.message_id

    # Look up paired user command message from DB
    user_msg_id = await db.get_user_message_for_bot_message(chat_id, bot_msg_id)

    # Delete bot message
    try:
        await callback.message.delete()
    except Exception:
        pass

    # Delete user's original command message
    if user_msg_id:
        try:
            await bot.delete_message(chat_id, user_msg_id)
        except Exception:
            pass

    await callback.answer()


# ── Inline search ──────────────────────────────────

@router.inline_query()
async def inline_search(query: InlineQuery):
    text = query.query.strip()

    if len(text) < 3:
        await query.answer(
            [],
            switch_pm_text="✦ Type at least 3 characters~",
            switch_pm_parameter="help",
            cache_time=1
        )
        return

    raw = await search_anime(text)

    if not raw:
        empty_id = hashlib.md5(f"empty:{text}".encode()).hexdigest()
        await query.answer(
            [InlineQueryResultArticle(
                id=empty_id,
                title="◈ Not found~",
                description=f"'{text}' isn't in the collection yet~",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        f"◈ mou~ <b>{text}</b> isn't available yet~\n"
                        f"✦ just type it in the group and i'll try my best~\n"
                        f"<i>{CREDIT_LINE}</i>"
                    ),
                    parse_mode="HTML"
                )
            )],
            cache_time=30
        )
        return

    enriched       = await enrich_results(raw[:8])
    inline_results = []

    for result in enriched:
        title  = result.get("title", "Unknown")
        rtype  = result.get("type", "")
        studio = result.get("studio", "")
        langs  = result.get("languages", "")
        url    = result.get("watch_url", "")
        mal_id = result.get("mal_id", "")
        poster = result.get("poster")

        card = search_result_card(result)
        kb   = detail_card_keyboard(watch_url=url, mal_id=mal_id)
        uid  = hashlib.md5(f"{title}:{mal_id}".encode()).hexdigest()

        inline_results.append(
            InlineQueryResultArticle(
                id=uid,
                title=f"✦ {title}",
                description=f"{rtype} • {studio} • {langs}",
                input_message_content=InputTextMessageContent(
                    message_text=card,
                    parse_mode="HTML"
                ),
                reply_markup=kb,
                thumbnail_url=poster,
            )
        )

    await query.answer(inline_results, cache_time=60)
