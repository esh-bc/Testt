# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   channel_db.py — Telegram Channel as Database
#   © AnimeTadka
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import json
from datetime import datetime
from aiogram import Bot
from config import LOG_CHANNEL_ID

TAG_AUTH    = "#AUTHORISED"
TAG_ADMIN   = "#ADMIN"
TAG_REQUEST = "#REQUEST"
TAG_SEARCH  = "#SEARCH"
TAG_REVOKE  = "#REVOKED"


async def log_authorised_group(bot: Bot, group_id: int, group_title: str, authorised_by: int):
    text = (
        f"{TAG_AUTH}\n"
        f"◈ Group ID: <code>{group_id}</code>\n"
        f"◈ Title: {group_title}\n"
        f"◈ By: <code>{authorised_by}</code>\n"
        f"◈ Time: {_now()}"
    )
    msg = await bot.send_message(LOG_CHANNEL_ID, text, parse_mode="HTML")
    return msg.message_id


async def log_revoked_group(bot: Bot, group_id: int):
    text = (
        f"{TAG_REVOKE}\n"
        f"◈ Group ID: <code>{group_id}</code>\n"
        f"◈ Time: {_now()}"
    )
    await bot.send_message(LOG_CHANNEL_ID, text, parse_mode="HTML")


async def log_admin(bot: Bot, user_id: int, added_by: int):
    text = (
        f"{TAG_ADMIN}\n"
        f"◈ Admin ID: <code>{user_id}</code>\n"
        f"◈ Added by: <code>{added_by}</code>\n"
        f"◈ Time: {_now()}"
    )
    msg = await bot.send_message(LOG_CHANNEL_ID, text, parse_mode="HTML")
    return msg.message_id


async def log_request(bot: Bot, user_id: int, username: str, anime: str, group_id: int, group_title: str):
    text = (
        f"{TAG_REQUEST}\n"
        f"◈ Anime: <b>{anime}</b>\n"
        f"◈ By: @{username} (<code>{user_id}</code>)\n"
        f"◈ Group: {group_title} (<code>{group_id}</code>)\n"
        f"◈ Time: {_now()}\n"
        f"◈ Status: PENDING"
    )
    msg = await bot.send_message(LOG_CHANNEL_ID, text, parse_mode="HTML")
    return msg.message_id


async def log_search(bot: Bot, user_id: int, username: str, query: str, results_count: int, group_id: int):
    text = (
        f"{TAG_SEARCH}\n"
        f"◈ Query: <b>{query}</b>\n"
        f"◈ Results: {results_count}\n"
        f"◈ By: @{username} (<code>{user_id}</code>)\n"
        f"◈ Group: <code>{group_id}</code>\n"
        f"◈ Time: {_now()}"
    )
    await bot.send_message(LOG_CHANNEL_ID, text, parse_mode="HTML")


def _now():
    return datetime.utcnow().strftime("%d %b %Y • %H:%M UTC")
