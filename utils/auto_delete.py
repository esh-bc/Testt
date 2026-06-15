# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   utils/auto_delete.py — Background deletion loop
#   © AnimeTadka
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import asyncio
import logging
from aiogram import Bot
from utils import db

log = logging.getLogger("YukiBot.AutoDelete")

DELETE_CHECK_INTERVAL = 60    # check every 60 seconds
CLEANUP_INTERVAL      = 3600  # cleanup DB every hour


async def _delete_safe(bot: Bot, chat_id: int, message_id: int | None):
    if not message_id:
        return
    try:
        await bot.delete_message(chat_id, message_id)
    except Exception:
        pass


async def _run_due_deletions(bot: Bot):
    """Fetch all due entries and delete the messages."""
    due = await db.get_due_deletions()
    for entry in due:
        chat_id    = entry["chat_id"]
        bot_msg_id = entry.get("bot_message_id")
        usr_msg_id = entry.get("user_message_id")

        await _delete_safe(bot, chat_id, bot_msg_id)
        await _delete_safe(bot, chat_id, usr_msg_id)
        await db.remove_deletion(entry["_id"])

    if due:
        log.info(f"Auto-deleted {len(due)} message pair(s)~")


async def auto_delete_loop(bot: Bot):
    """
    Long-running background coroutine.
    Every 60s: delete due messages.
    Every hour: clean up old DB entries.
    """
    log.info("Auto-delete loop started~")
    elapsed = 0

    while True:
        await asyncio.sleep(DELETE_CHECK_INTERVAL)
        elapsed += DELETE_CHECK_INTERVAL

        try:
            await _run_due_deletions(bot)
        except Exception as e:
            log.warning(f"Auto-delete run error: {e}")

        if elapsed >= CLEANUP_INTERVAL:
            elapsed = 0
            try:
                removed = await db.cleanup_old_deletions()
                if removed:
                    log.info(f"DB cleanup: removed {removed} old deletion entries~")
            except Exception as e:
                log.warning(f"DB cleanup error: {e}")
