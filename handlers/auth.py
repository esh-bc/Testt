# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   handlers/auth.py — /authorise /revoke
#   © AnimeTadka
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import uuid
from aiogram import Router, Bot, F
from aiogram.types import (
    Message, CallbackQuery,
    ChatMemberAdministrator, ChatMemberOwner,
    ChatMemberUpdated
)
from aiogram.filters import Command
from aiogram.enums import ChatType

from utils.messages import (
    authorise_success_msg,
    ANON_VERIFY_MSG, ALREADY_AUTHORISED,
    REVOKE_SUCCESS, DIV, DIV2, GROUP_WELCOME
)
from utils.keyboards import anon_verify_keyboard
from utils.state import (
    is_group_authorised, authorise_group_memory, revoke_group_memory,
    is_bot_admin, store_anon_verification, pop_anon_verification
)
from utils import db
from config import CREDIT_LINE, AUTO_DELETE_DELAY, OWNER_ID

router = Router()

PRIVATE_REPLY = (
    "✦ ara ara~ you found me in private~\n"
    "◈ how bold~ but i only work in groups~\n"
    "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\n"
    f"<i>{CREDIT_LINE}</i>"
)


def _mention(user) -> str:
    if user and user.username:
        return f"@{user.username}"
    if user:
        return f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"
    return "unknown"


def _is_privileged(user) -> bool:
    """Owner or bot admin."""
    if user is None:
        return False
    return user.id == OWNER_ID or is_bot_admin(user.id)


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


async def _is_group_admin(bot: Bot, chat_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return isinstance(member, (ChatMemberAdministrator, ChatMemberOwner))
    except Exception:
        return False


# ── /authorise ────────────────────────────────────

@router.message(Command("authorise"))
async def cmd_authorise(message: Message, bot: Bot):
    user  = message.from_user
    parts = message.text.split(maxsplit=1)
    arg   = parts[1].strip() if len(parts) > 1 else None

    # ── Remote authorise via argument ─────────────
    if arg:
        try:
            target_id = int(arg)
        except ValueError:
            target_id = None

        if target_id is not None:
            if not _is_privileged(user):
                sent = await message.reply(
                    "◈ mou~ you're not allowed to do that~",
                    parse_mode="HTML"
                )
                await _schedule(sent, message.message_id)
                return

            if is_group_authorised(target_id):
                sent = await message.reply(ALREADY_AUTHORISED[0], parse_mode="HTML")
                await _schedule(sent, message.message_id)
                return

            authorise_group_memory(target_id)
            await db.authorise_group(target_id, f"Remote({target_id})", user.id)
            sent = await message.reply(
                f"✦ ara ara~ group <code>{target_id}</code> is now in my circle~\n"
                f"◈ they better behave~",
                parse_mode="HTML"
            )
            await _schedule(sent, message.message_id)
            return

    # ── Private — no remote arg given ─────────────
    if message.chat.type == ChatType.PRIVATE:
        sent = await message.reply(PRIVATE_REPLY, parse_mode="HTML")
        await _schedule(sent, message.message_id)
        return

    # ── Group flow ─────────────────────────────────
    if user is None:
        key = str(uuid.uuid4())[:8]
        store_anon_verification(key, {
            "action":      "authorise",
            "group_id":    message.chat.id,
            "group_title": message.chat.title or "Unknown"
        })
        sent = await message.reply(
            ANON_VERIFY_MSG,
            parse_mode="HTML",
            reply_markup=anon_verify_keyboard(key)
        )
        await _schedule(sent, message.message_id)
        return

    if not is_bot_admin(user.id) and not await _is_group_admin(bot, message.chat.id, user.id):
        sent = await message.reply(
            f"◈ ara ara~ {_mention(user)} only admins can do that~\n✦ nice try~",
            parse_mode="HTML"
        )
        await _schedule(sent, message.message_id)
        return

    if is_group_authorised(message.chat.id):
        sent = await message.reply(ALREADY_AUTHORISED[0], parse_mode="HTML")
        await _schedule(sent, message.message_id)
        return

    authorise_group_memory(message.chat.id)
    await db.authorise_group(message.chat.id, message.chat.title or "Unknown", user.id)

    sent = await message.reply(
        f"{authorise_success_msg()}\n{DIV}\n{GROUP_WELCOME(message.chat.title or 'this group')}",
        parse_mode="HTML"
    )
    await _schedule(sent, message.message_id)


# ── /revoke ───────────────────────────────────────

@router.message(Command("revoke"))
async def cmd_revoke(message: Message, bot: Bot):
    user  = message.from_user
    parts = message.text.split(maxsplit=1)
    arg   = parts[1].strip() if len(parts) > 1 else None

    # ── Remote revoke via argument ─────────────────
    if arg:
        try:
            target_id = int(arg)
        except ValueError:
            target_id = None

        if target_id is not None:
            if not _is_privileged(user):
                sent = await message.reply(
                    "◈ mou~ you're not allowed to do that~",
                    parse_mode="HTML"
                )
                await _schedule(sent, message.message_id)
                return

            revoke_group_memory(target_id)
            await db.revoke_group(target_id)
            sent = await message.reply(
                f"◇ fine~ <code>{target_id}</code> has been removed from my list~\n"
                f"✦ their loss~",
                parse_mode="HTML"
            )
            await _schedule(sent, message.message_id)
            return

    # ── Private — no remote arg given ─────────────
    if message.chat.type == ChatType.PRIVATE:
        sent = await message.reply(PRIVATE_REPLY, parse_mode="HTML")
        await _schedule(sent, message.message_id)
        return

    # ── Group flow ─────────────────────────────────
    if user is None:
        key = str(uuid.uuid4())[:8]
        store_anon_verification(key, {
            "action":      "revoke",
            "group_id":    message.chat.id,
            "group_title": message.chat.title or "Unknown"
        })
        sent = await message.reply(
            ANON_VERIFY_MSG,
            parse_mode="HTML",
            reply_markup=anon_verify_keyboard(key)
        )
        await _schedule(sent, message.message_id)
        return

    if not is_bot_admin(user.id) and not await _is_group_admin(bot, message.chat.id, user.id):
        sent = await message.reply(
            f"◈ mou~ {_mention(user)} not your call to make~",
            parse_mode="HTML"
        )
        await _schedule(sent, message.message_id)
        return

    revoke_group_memory(message.chat.id)
    await db.revoke_group(message.chat.id)
    sent = await message.reply(REVOKE_SUCCESS[0], parse_mode="HTML")
    await _schedule(sent, message.message_id)


# ── Anon verify callback ───────────────────────────

@router.callback_query(F.data.startswith("anon_verify:"))
async def anon_verify_callback(callback: CallbackQuery, bot: Bot):
    key  = callback.data.split(":", 1)[1]
    data = pop_anon_verification(key)

    if not data:
        await callback.answer("◈ verification expired~ try again~", show_alert=True)
        return

    user     = callback.from_user
    group_id = data["group_id"]

    if not await _is_group_admin(bot, group_id, user.id) and not is_bot_admin(user.id):
        await callback.answer(
            "◈ ara ara~ you're not an admin~\n✦ nice try~",
            show_alert=True
        )
        return

    if data["action"] == "authorise":
        if is_group_authorised(group_id):
            await callback.answer("◈ already authorised~", show_alert=True)
            return
        authorise_group_memory(group_id)
        await db.authorise_group(group_id, data["group_title"], user.id)
        await callback.message.edit_text(
            f"{authorise_success_msg()}\n{DIV}\n<i>{CREDIT_LINE}</i>",
            parse_mode="HTML"
        )

    elif data["action"] == "revoke":
        revoke_group_memory(group_id)
        await db.revoke_group(group_id)
        await callback.message.edit_text(
            f"◇ verified~ group unauthorised~\n<i>{CREDIT_LINE}</i>",
            parse_mode="HTML"
        )

    await callback.answer("✦ verified~")


# ── Bot added to group ─────────────────────────────

@router.my_chat_member()
async def bot_added_to_group(event: ChatMemberUpdated, bot: Bot):
    try:
        if event.new_chat_member.user.id != (await bot.get_me()).id:
            return
        new_status = event.new_chat_member.status
        old_status = event.old_chat_member.status
        if new_status not in ("member", "administrator"):
            return
        if old_status in ("member", "administrator"):
            return
        chat = event.chat
        if chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
            return
        await bot.send_message(
            chat.id,
            (
                f"✦ ara ara~ yuki has arrived~\n"
                f"{DIV}\n"
                f"◈ to unlock me~ an admin must use /authorise~\n"
                f"◇ until then~ i'll just sit here looking pretty~\n"
                f"{DIV2}\n"
                f"<i>{CREDIT_LINE}</i>"
            ),
            parse_mode="HTML"
        )
    except Exception:
        pass
