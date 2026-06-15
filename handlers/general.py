# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   handlers/general.py — /start /help /new
#   © AnimeTadka
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from aiogram.enums import ChatType

from utils.messages import HELP_MSG, DIV, DIV2
from utils.state import is_bot_admin
from utils import db
from config import CREDIT_LINE, AUTO_DELETE_DELAY, OWNER_ID

router = Router()

PRIVATE_REPLY = (
    "✦ ara ara~ you found me in private~\n"
    "◈ how bold~ but i only work in groups~\n"
    f"┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\n"
    f"<i>{CREDIT_LINE}</i>"
)


def _is_privileged(user) -> bool:
    """Owner or bot admin — can use bot in private."""
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


@router.message(CommandStart())
async def cmd_start(message: Message):
    if message.chat.type == ChatType.PRIVATE:
        if not _is_privileged(message.from_user):
            sent = await message.reply(PRIVATE_REPLY, parse_mode="HTML")
            await _schedule(sent, message.message_id)
            return
    sent = await message.reply(
        f"✦ ara ara~ yuki awakens~\n"
        f"◈ use /help to see what i can do~\n"
        f"<i>{CREDIT_LINE}</i>",
        parse_mode="HTML"
    )
    await _schedule(sent, message.message_id)


@router.message(Command("help"))
async def cmd_help(message: Message):
    if message.chat.type == ChatType.PRIVATE:
        if not _is_privileged(message.from_user):
            sent = await message.reply(PRIVATE_REPLY, parse_mode="HTML")
            await _schedule(sent, message.message_id)
            return
    sent = await message.reply(HELP_MSG(), parse_mode="HTML")
    await _schedule(sent, message.message_id)


@router.message(Command("new"))
async def cmd_new(message: Message):
    if message.chat.type == ChatType.PRIVATE:
        if not _is_privileged(message.from_user):
            sent = await message.reply(PRIVATE_REPLY, parse_mode="HTML")
            await _schedule(sent, message.message_id)
            return
    sent = await message.reply(
        f"✦ ara ara~ new arrivals~\n"
        f"{DIV}\n"
        f"◈ this feature is coming soon~\n"
        f"◇ for now~ just type any anime name in the group~\n"
        f"{DIV2}\n"
        f"<i>{CREDIT_LINE}</i>",
        parse_mode="HTML"
    )
    await _schedule(sent, message.message_id)
