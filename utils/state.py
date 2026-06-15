# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   state.py — In-memory state
#   © AnimeTadka
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import time
from collections import defaultdict
from config import OWNER_ID, RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW

# Loaded from MongoDB on startup
authorised_groups: set[int] = set()
bot_admins:        set[int] = set()

# Pending anon verifications { key: {action, group_id, group_title} }
pending_anon_verifications: dict = {}

# Rate limit buckets { (group_id, user_id): [timestamps] }
_rate_buckets: dict = defaultdict(list)


def is_group_authorised(group_id: int) -> bool:
    return group_id in authorised_groups


def authorise_group_memory(group_id: int):
    authorised_groups.add(group_id)


def revoke_group_memory(group_id: int):
    authorised_groups.discard(group_id)


def is_bot_admin(user_id: int) -> bool:
    return user_id == OWNER_ID or user_id in bot_admins


def add_bot_admin_memory(user_id: int):
    bot_admins.add(user_id)


def check_rate_limit(group_id: int, user_id: int) -> tuple[bool, int]:
    key = (group_id, user_id)
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW
    _rate_buckets[key] = [t for t in _rate_buckets[key] if t > window_start]
    if len(_rate_buckets[key]) >= RATE_LIMIT_REQUESTS:
        oldest = _rate_buckets[key][0]
        wait   = int(RATE_LIMIT_WINDOW - (now - oldest)) + 1
        return False, wait
    _rate_buckets[key].append(now)
    return True, 0


def store_anon_verification(key: str, data: dict):
    pending_anon_verifications[key] = data


def pop_anon_verification(key: str) -> dict | None:
    return pending_anon_verifications.pop(key, None)
