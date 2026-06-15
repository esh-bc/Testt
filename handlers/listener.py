# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   handlers/listener.py — Group message auto-listener
#   © AnimeTadka
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import logging

from aiogram import Router, Bot, F
from aiogram.types import Message
from aiogram.enums import ChatType
from rapidfuzz import fuzz, process

from utils.db import get_fuzzy_cache, schedule_deletion
from utils.api import search_anime, enrich_results, search_jikan
from utils.messages import search_result_card, DIV2
from utils.keyboards import detail_card_keyboard, no_results_keyboard
from utils.state import is_group_authorised
from config import AUTO_DELETE_DELAY, CREDIT_LINE

# Import the shared no-result query store from search handler
from handlers.search import _no_result_query, _cache_key

router = Router()
log    = logging.getLogger("YukiBot.Listener")

_FUZZY_THRESHOLD = 75


async def _schedule(bot_msg: Message, user_msg_id: int | None = None):
    try:
        await schedule_deletion(
            chat_id=bot_msg.chat.id,
            bot_message_id=bot_msg.message_id,
            user_message_id=user_msg_id,
            delay_seconds=AUTO_DELETE_DELAY
        )
    except Exception:
        pass


@router.message(
    F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}),
    F.text
)
async def group_listener(message: Message, bot: Bot):
    """
    Passive listener for group messages.
    Runs fuzzy matching against the local anime index cache.
    Falls back to AT API → Jikan. Silent ignore if nothing matches.
    """
    try:
        # ── Gate checks ────────────────────────────────────
        text = (message.text or "").strip()
        if not text:
            return

        if len(text) < 3 or len(text) > 100:
            return

        if not is_group_authorised(message.chat.id):
            return

        # ── STEP 1 — Local Fuzzy Filter ────────────────────
        cache = get_fuzzy_cache()

        if cache:
            titles  = [e.get("title", "")    for e in cache]
            indexes = [e.get("ai_index", "") for e in cache]

            match_title = process.extractOne(
                text, titles,  scorer=fuzz.partial_ratio
            )
            match_index = process.extractOne(
                text, indexes, scorer=fuzz.partial_ratio
            )

            score_title = match_title[1] if match_title else 0
            score_index = match_index[1] if match_index else 0
            best_score  = max(score_title, score_index)

            # Keep the cache-matched title for the later confidence check
            if score_title >= score_index:
                best_cache_title = match_title[0] if match_title else ""
            else:
                best_cache_title = match_index[0] if match_index else ""
        else:
            best_score        = 0
            best_cache_title  = ""

        # Score below threshold — silent ignore, no Jikan
        if best_score < _FUZZY_THRESHOLD:
            return

        # ── STEP 2 — AT API + TMDB Enrich ─────────────────
        raw = await search_anime(text)

        if raw is None or len(raw) == 0:
            # AT API returned nothing — try Jikan fallback
            await _handle_jikan_fallback(message, text)
            return

        await bot.send_chat_action(message.chat.id, "typing")
        enriched = await enrich_results(raw)

        if not enriched:
            await _handle_jikan_fallback(message, text)
            return

        # ── Confidence check — ensure top result actually matches ──
        # Score against BOTH the raw user text AND the cache-matched title
        # (handles JP title → EN title mappings like "kimetsu no yaiba" → "Demon Slayer")
        result       = enriched[0]
        result_title = result.get("title", "")

        score_vs_query = process.extractOne(
            text, [result_title], scorer=fuzz.partial_ratio
        )
        score_vs_cache = process.extractOne(
            best_cache_title, [result_title], scorer=fuzz.partial_ratio
        ) if best_cache_title else None

        conf_score = max(
            score_vs_query[1] if score_vs_query else 0,
            score_vs_cache[1] if score_vs_cache else 0,
        )

        if conf_score < 60:
            log.debug(
                f"AT API result '{result_title}' confidence {conf_score} < 60 "
                f"(query='{text}', cache_match='{best_cache_title}') — falling through to Jikan"
            )
            await _handle_jikan_fallback(message, text)
            return

        # Send the top result as a card
        card   = search_result_card(result)
        kb     = detail_card_keyboard(
            watch_url=result.get("watch_url", ""),
            mal_id=result.get("mal_id")
        )
        poster = result.get("poster")

        if poster:
            try:
                sent = await message.reply_photo(
                    photo=poster,
                    caption=card,
                    parse_mode="HTML",
                    reply_markup=kb
                )
                await _schedule(sent, message.message_id)
                return
            except Exception:
                pass

        sent = await message.reply(card, parse_mode="HTML", reply_markup=kb)
        await _schedule(sent, message.message_id)

    except Exception as e:
        log.warning(f"group_listener unhandled exception: {e}")


async def _handle_jikan_fallback(message: Message, text: str):
    """STEP 3 — Try Jikan. If nothing found, silently ignore (STEP 4)."""
    try:
        jikan_result = await search_jikan(text)

        if not jikan_result:
            # STEP 4 — Silent ignore
            return

        jikan_title = jikan_result.get("title", text)

        # ── Second AT API attempt using the clean Jikan title ──
        raw2 = await search_anime(jikan_title)
        if raw2:
            await message.bot.send_chat_action(message.chat.id, "typing")
            enriched2 = await enrich_results(raw2)
            if enriched2:
                # Confidence check: score against original text AND Jikan title
                r2_title = enriched2[0].get("title", "")
                s1 = process.extractOne(text,        [r2_title], scorer=fuzz.partial_ratio)
                s2 = process.extractOne(jikan_title, [r2_title], scorer=fuzz.partial_ratio)
                conf2 = max(s1[1] if s1 else 0, s2[1] if s2 else 0)
                if conf2 < 60:
                    log.debug(
                        f"Second AT result '{r2_title}' confidence {conf2} < 60 "
                        f"(jikan='{jikan_title}') — falling through to not-in-collection"
                    )
                    enriched2 = []

            if enriched2:
                result = enriched2[0]
                card   = search_result_card(result)
                kb     = detail_card_keyboard(
                    watch_url=result.get("watch_url", ""),
                    mal_id=result.get("mal_id")
                )
                poster = result.get("poster")
                if poster:
                    try:
                        sent = await message.reply_photo(
                            photo=poster,
                            caption=card,
                            parse_mode="HTML",
                            reply_markup=kb
                        )
                        await schedule_deletion(
                            chat_id=sent.chat.id,
                            bot_message_id=sent.message_id,
                            user_message_id=message.message_id,
                            delay_seconds=AUTO_DELETE_DELAY
                        )
                        return
                    except Exception:
                        pass
                sent = await message.reply(card, parse_mode="HTML", reply_markup=kb)
                await schedule_deletion(
                    chat_id=sent.chat.id,
                    bot_message_id=sent.message_id,
                    user_message_id=message.message_id,
                    delay_seconds=AUTO_DELETE_DELAY
                )
                return

        # Second AT API also empty — show "not in collection" message
        # Store the original query so auto_req callback can use it
        key = _cache_key(message.chat.id, message.from_user.id)
        _no_result_query[key] = text

        sent = await message.reply(
            f"✦ ara ara~ <b>{jikan_title}</b> rings a bell~\n"
            f"◈ mou~ it's not in our collection yet~\n"
            f"◇ but don't worry~ i'll haunt the owner until it appears~\n"
            f"{DIV2}\n"
            f"<i>{CREDIT_LINE}</i>",
            parse_mode="HTML",
            reply_markup=no_results_keyboard()
        )
        await schedule_deletion(
            chat_id=sent.chat.id,
            bot_message_id=sent.message_id,
            user_message_id=message.message_id,
            delay_seconds=AUTO_DELETE_DELAY
        )

    except Exception as e:
        log.warning(f"_handle_jikan_fallback error: {e}")
