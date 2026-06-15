# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   handlers/request.py — request prompt callback
#   © AnimeTadka
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from aiogram import Router, F
from aiogram.types import CallbackQuery

router = Router()


@router.callback_query(F.data == "req_prompt")
async def req_prompt(callback: CallbackQuery):
    await callback.answer(
        "◈ just type the anime name in the group~ i'll notice it~",
        show_alert=True
    )
