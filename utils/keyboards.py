# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   keyboards.py — All colourful keyboards
#   © AnimeTadka
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import PAGE_SIZE


def _btn(text: str, url: str = None, callback_data: str = None, style: str = None) -> InlineKeyboardButton:
    kwargs = {"text": text}
    if url:
        kwargs["url"] = url
    if callback_data:
        kwargs["callback_data"] = callback_data
    if style:
        kwargs["style"] = style
    return InlineKeyboardButton(**kwargs)


# ── Search list keyboard — paginated title buttons ─

def search_list_keyboard(results: list[dict], page: int, query: str) -> InlineKeyboardMarkup:
    """
    Shows PAGE_SIZE title buttons per page.
    Each button callback: select:{index}:{query}
    Bottom row: Prev / Next + Close
    """
    builder = InlineKeyboardBuilder()
    total   = len(results)
    start   = page * PAGE_SIZE
    end     = min(start + PAGE_SIZE, total)
    page_results = results[start:end]

    for i, result in enumerate(page_results):
        actual_index = start + i
        title = result.get("title", "Unknown")
        display = title if len(title) <= 35 else title[:32] + "..."
        builder.row(
            _btn(f"◈ {display}", callback_data=f"select:{actual_index}:{query}", style="primary")
        )

    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
    nav = []
    if page > 0:
        nav.append(_btn("◁ Prev", callback_data=f"page:{page - 1}:{query}", style="primary"))
    if page < total_pages - 1:
        nav.append(_btn("Next ▷", callback_data=f"page:{page + 1}:{query}", style="primary"))
    if nav:
        builder.row(*nav)

    builder.row(
        _btn(f"◇ Page {page + 1} of {total_pages}", callback_data="noop", style="primary"),
    )
    builder.row(
        _btn("✦ Close ✕", callback_data="close_result", style="danger")
    )

    return builder.as_markup()


# ── Detail card keyboard — after user picks a title ─

def detail_card_keyboard(watch_url: str, mal_id: str = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        _btn("◉ Watch Now ▸", url=watch_url, style="success")
    )
    if mal_id:
        builder.row(
            _btn("◇ MAL Page ▸", url=f"https://myanimelist.net/anime/{mal_id}", style="primary")
        )
    builder.row(
        _btn("✦ Close ✕", callback_data="close_result", style="danger")
    )
    return builder.as_markup()


# ── No results keyboard — auto-request button ──────
# The query is stored in memory; callback is just "auto_req"
# so we stay well within Telegram's 64-byte callback_data limit.

def no_results_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        _btn("◈ Request This Anime ▸", callback_data="auto_req", style="primary")
    )
    builder.row(
        _btn("✦ Close ✕", callback_data="close_result", style="danger")
    )
    return builder.as_markup()


# ── Anon verify keyboard ───────────────────────────

def anon_verify_keyboard(callback_key: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        _btn("✦ Verify I'm Admin ◉", callback_data=f"anon_verify:{callback_key}", style="success")
    )
    builder.row(
        _btn("◇ Cancel ✕", callback_data="close_result", style="danger")
    )
    return builder.as_markup()


# ── Admin request management ───────────────────────

def admin_requests_keyboard(request_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        _btn("◉ Mark Added ✦", callback_data=f"done_req:{request_id}", style="success"),
        _btn("◇ Dismiss ✕",    callback_data=f"dismiss_req:{request_id}", style="danger")
    )
    return builder.as_markup()


# ── Request confirm keyboard ───────────────────────

def request_confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        _btn("✦ Close ✕", callback_data="close_result", style="danger")
    )
    return builder.as_markup()
