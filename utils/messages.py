# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   messages.py — Yuki personality & all bot text
#   © AnimeTadka
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import random
from config import CREDIT_LINE

DIV  = "─────────────────────────"
DIV2 = "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄"

SEARCH_OPENERS = [
    "ara ara~ {mention} actually knows what they want ✦",
    "mou~ {mention} dragged me out of my nap for THIS? fine ◈",
    "✦ oh? {mention} has taste~ let me check my archives",
    "◇ {mention} asked nicely enough~ i suppose i'll help",
    "nani?! {mention} wants anime? how original~ ▸",
    "✦ {mention} you rang? i was busy being perfect but fine~",
    "ara~ {mention} thinks i work for them now~ how cute ◈",
]

NO_RESULT_OPENERS = [
    "mou~~ {mention} that's NOT in my collection ✦",
    "◈ nani?! even i haven't heard of that one {mention}~",
    "ara ara~ {mention} searched for something that doesn't exist here yet ◇",
    "✦ {mention} my database weeps~ it's not there~",
]

RATE_LIMIT_MSGS = [
    "◈ mou~~ {mention} slow DOWN i'm not a vending machine ✦\n▸ come back in {wait}s baka~",
    "✦ {mention} NANI you again?! wait {wait} seconds onegai~",
    "ara~ {mention} so impatient~ {wait}s~ that's your punishment ◇",
]

PRIVATE_CHAT_MSGS = [
    "◈ mou~ i only perform for an audience~\n✦ add me to a group first baka~",
    "ara ara~ a private chat? how bold~\n◇ but i work in groups only~",
    "✦ nani?! you think i'll work alone?\n◈ add me to a group~ then we'll talk~",
]

UNAUTHORISED_MSGS = [
    "◈ ara~ this group hasn't been unlocked yet~\n✦ an admin needs to use /authorise first~",
    "mou~ {mention} i'm on vacation here~\n◈ get an admin to /authorise this group first~",
]

AUTHORISE_SUCCESS = [
    "✦ ara ara~ fine fine i'll grace this group with my presence~\n◈ yuki has entered the chat properly now~",
    "◈ mou~ took you long enough~\n✦ yuki is NOW accepting anime searches here~",
]

REVOKE_SUCCESS = [
    "◇ ara~ and just like that i'm gone~\n✦ this group has been unauthorised~ sayonara~",
]

REQUEST_SUCCESS = [
    "✦ ara~ {mention} wants <b>{anime}</b>~\n◈ noted~ i'll haunt the owner until they add it~\n◇ don't hold your breath though~",
    "◈ {mention} filed a request for <b>{anime}</b>~\n✦ your wish has been logged~ ara ara~",
]

ADMIN_ADDED = [
    "✦ ara ara~ <code>{uid}</code> is now a bot admin~\n◈ don't let it go to their head~",
]

ALREADY_AUTHORISED = [
    "◈ mou~ this group is already in my good books~\n✦ no need to ask twice baka~",
]

ANON_VERIFY_MSG = (
    "✦ ara ara~ an anonymous admin~\n"
    "◈ how mysterious~ tap below to prove you're worthy~\n"
    f"{DIV2}"
)

HELP_MSG = lambda: (
    f"✦ ara ara~ you need <b>yuki's help</b>? how cute~\n"
    f"{DIV}\n"
    f"◈ just type an anime name in the group~\n"
    f"◇ i'll notice it automatically~ ara ara~\n"
    f"◈ <b>/new</b> — see what's fresh~\n"
    f"◇ <b>/help</b> — you're already here baka~\n"
    f"{DIV2}\n"
    f"✦ <b>Admin Only~</b>\n"
    f"◈ /authorise [group_id] — unlock a group~\n"
    f"◇ /revoke [group_id] — kick me out~\n"
    f"◈ /addadmin &lt;user_id&gt; — promote someone~\n"
    f"◇ /requests — see pending requests~\n"
    f"◈ /stats — usage stats~\n"
    f"{DIV}\n"
    f"<i>{CREDIT_LINE}</i>"
)

GROUP_WELCOME = lambda title: (
    f"✦ ara ara~ yuki has arrived in <b>{title}</b>~\n"
    f"{DIV}\n"
    f"◈ she did NOT come to play~\n"
    f"◇ well~ maybe a little~\n"
    f"✦ just type an anime name~ i'll find it~\n"
    f"◈ no commands needed~ i'm always watching~\n"
    f"◇ don't spam me~ i bite~\n"
    f"{DIV2}\n"
    f"<i>{CREDIT_LINE}</i>"
)


def search_list_header(mention: str, query: str, total: int) -> str:
    opener = random.choice(SEARCH_OPENERS).format(mention=mention)
    return (
        f"{opener}\n"
        f"{DIV}\n"
        f"◇ Query ▸ <b>{query}</b>\n"
        f"◈ Found ▸ <b>{total}</b> results~\n"
        f"{DIV2}\n"
        f"◇ tap a title to see details~"
    )


def search_result_card(result: dict) -> str:
    title = result.get("title", "Unknown")
    langs = result.get("languages", "")

    text = (
        f"✦ <b>{title}</b>\n"
        f"{DIV}\n"
    )
    if langs:
        text += f"◇ Audio ▸ {langs}\n"

    text += f"{DIV}\n<i>{CREDIT_LINE}</i>"
    return text


def no_results_msg(mention: str, query: str) -> str:
    opener = random.choice(NO_RESULT_OPENERS).format(mention=mention)
    return (
        f"{opener}\n"
        f"{DIV}\n"
        f"◇ <b>{query}</b> isn't in the collection yet~\n"
        f"◈ tap below to request it~\n"
        f"{DIV2}\n"
        f"<i>{CREDIT_LINE}</i>"
    )


def rate_limit_msg(mention: str, wait: int) -> str:
    return random.choice(RATE_LIMIT_MSGS).format(mention=mention, wait=wait)


def search_opener(mention: str) -> str:
    return random.choice(SEARCH_OPENERS).format(mention=mention)


def unauthorised_msg(mention: str = "") -> str:
    return random.choice(UNAUTHORISED_MSGS).format(mention=mention)


def private_msg() -> str:
    return random.choice(PRIVATE_CHAT_MSGS)


def authorise_success_msg() -> str:
    return random.choice(AUTHORISE_SUCCESS)


def request_success_msg(mention: str, anime: str) -> str:
    return random.choice(REQUEST_SUCCESS).format(mention=mention, anime=anime)


def admin_added_msg(uid: int) -> str:
    return random.choice(ADMIN_ADDED).format(uid=uid)
