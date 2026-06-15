# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   handlers/admin.py — Admin commands
#   © AnimeTadka
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from utils.messages import admin_added_msg, DIV, DIV2
from utils.keyboards import admin_requests_keyboard
from utils.state import is_bot_admin, add_bot_admin_memory
from utils import db
from config import CREDIT_LINE, OWNER_ID, AUTO_DELETE_DELAY

router = Router()


def _mention(user) -> str:
    if user and user.username:
        return f"@{user.username}"
    if user:
        return f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"
    return "unknown"


def _is_owner(user) -> bool:
    return user is not None and user.id == OWNER_ID


def _is_admin(user) -> bool:
    return user is not None and is_bot_admin(user.id)


async def _schedule(bot_msg: Message, user_msg_id: int | None = None):
    try:
        await db.schedule_deletion(
            chat_id=bot_msg.chat.id,
            bot_message_id=bot_msg.message_id,
            user_message_id=user_msg_id,
            delay_seconds=AUTO_DELETE_DELAY
        )
    except Exception:
        pass


# ── /addadmin ─────────────────────────────────────

@router.message(Command("addadmin"))
async def cmd_addadmin(message: Message, bot: Bot):
    user = message.from_user
    if not _is_owner(user):
        sent = await message.reply(
            f"◈ ara ara~ only the owner can do that~\n✦ not you {_mention(user)}~",
            parse_mode="HTML"
        )
        await _schedule(sent, message.message_id)
        return

    parts = message.text.split()
    if len(parts) < 2:
        sent = await message.reply(
            f"◇ mou~ give me a user ID~\n◈ usage: <b>/addadmin 123456789</b>",
            parse_mode="HTML"
        )
        await _schedule(sent, message.message_id)
        return

    try:
        uid = int(parts[1])
    except ValueError:
        sent = await message.reply("◈ that's not a valid ID baka~", parse_mode="HTML")
        await _schedule(sent, message.message_id)
        return

    add_bot_admin_memory(uid)
    await db.add_admin(uid, user.id)
    sent = await message.reply(admin_added_msg(uid), parse_mode="HTML")
    await _schedule(sent, message.message_id)


# ── /requests ─────────────────────────────────────

@router.message(Command("requests"))
async def cmd_requests(message: Message):
    user = message.from_user
    if not _is_admin(user):
        sent = await message.reply(
            f"◈ ara~ {_mention(user)} admin eyes only~\n✦ shoo~",
            parse_mode="HTML"
        )
        await _schedule(sent, message.message_id)
        return

    pending = await db.get_pending_requests()

    if not pending:
        sent = await message.reply(
            f"✦ ara ara~ no pending requests~\n◈ the queue is empty~ for now~",
            parse_mode="HTML"
        )
        await _schedule(sent, message.message_id)
        return

    sent = await message.reply(
        f"✦ ara~ <b>{len(pending)}</b> pending requests~\n"
        f"◈ here they are~\n{DIV}",
        parse_mode="HTML"
    )
    await _schedule(sent, message.message_id)

    for req in pending:
        text = (
            f"◈ <b>{req['anime']}</b>\n"
            f"◇ By ▸ {req['user']}\n"
            f"◈ Group ▸ {req['group']}\n"
            f"✦ Time ▸ {req['time']}\n"
            f"{DIV2}"
        )
        item_sent = await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=admin_requests_keyboard(req["id"])
        )
        await _schedule(item_sent)


# ── /stats ─────────────────────────────────────────

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    user = message.from_user
    if not _is_admin(user):
        sent = await message.reply(
            f"◈ ara~ stats are for admins only {_mention(user)}~",
            parse_mode="HTML"
        )
        await _schedule(sent, message.message_id)
        return

    stats = await db.get_search_stats()
    total = stats["total"]
    top   = stats["top"]

    top_lines = ""
    for i, (term, count) in enumerate(top, 1):
        top_lines += f"◈ {i}. <b>{term}</b> — {count} searches\n"

    sent = await message.reply(
        f"✦ yuki's stats~ ara ara~\n"
        f"{DIV}\n"
        f"◇ Total Searches ▸ <b>{total}</b>\n"
        f"{DIV2}\n"
        f"✦ Top Searches~\n"
        f"{top_lines or '◈ nothing yet~'}"
        f"{DIV}\n"
        f"<i>{CREDIT_LINE}</i>",
        parse_mode="HTML"
    )
    await _schedule(sent, message.message_id)


# ── Request callbacks ──────────────────────────────

@router.callback_query(F.data.startswith("done_req:"))
async def done_request(callback: CallbackQuery):
    if not _is_admin(callback.from_user):
        await callback.answer("◈ admins only~", show_alert=True)
        return

    request_id = callback.data.split(":", 1)[1]
    await db.mark_request_done(request_id)
    await callback.message.edit_text(
        f"◉ ara ara~ marked as added~\n✦ one more for the collection~\n"
        f"<i>{CREDIT_LINE}</i>",
        parse_mode="HTML"
    )
    await callback.answer("✦ done~")


@router.callback_query(F.data.startswith("dismiss_req:"))
async def dismiss_request(callback: CallbackQuery):
    if not _is_admin(callback.from_user):
        await callback.answer("◈ admins only~", show_alert=True)
        return

    request_id = callback.data.split(":", 1)[1]
    await db.dismiss_request(request_id)
    await callback.message.edit_text(
        f"◇ dismissed~\n<i>{CREDIT_LINE}</i>",
        parse_mode="HTML"
    )
    await callback.answer("◈ dismissed~")
