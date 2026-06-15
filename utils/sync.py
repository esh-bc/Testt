# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   utils/sync.py — AnimeTadka index sync utilities
#   © AnimeTadka
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import asyncio
import logging
import aiohttp

from utils.db import save_anime_batch, upsert_anime, load_fuzzy_cache
from config import SEARCH_API_URL

log = logging.getLogger("YukiBot.Sync")

_HEADERS = {"User-Agent": "YukiBot/1.0"}
_SYNC_ALL_URL    = f"{SEARCH_API_URL}?mode=sync_all"
_SYNC_LATEST_URL = f"{SEARCH_API_URL}?mode=sync_latest"


async def sync_all_pages():
    """
    Loop GET requests to the sync_all endpoint page by page.
    Stops when response contains has_more: false.
    Logs progress every 10 pages. Refreshes fuzzy cache after completion.
    """
    log.info("sync_all_pages starting~")
    page         = 1
    total_so_far = 0

    async with aiohttp.ClientSession(headers=_HEADERS) as session:
        while True:
            try:
                async with session.get(
                    _SYNC_ALL_URL,
                    params={"page": page},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 429:
                        log.warning(f"sync_all page {page} — rate limited, waiting 5s~")
                        await asyncio.sleep(5)
                        continue

                    if resp.status != 200:
                        log.warning(f"sync_all page {page} — unexpected status {resp.status}, skipping~")
                        page += 1
                        continue

                    data = await resp.json()

            except Exception as e:
                log.error(f"sync_all page {page} — exception: {e}")
                page += 1
                continue

            entries  = data.get("data", [])
            has_more = data.get("has_more", False)

            if entries:
                await save_anime_batch(entries)
                total_so_far += len(entries)

            if page % 10 == 0:
                log.info(f"Synced page {page}, total so far: {total_so_far}")

            if not has_more:
                log.info(f"sync_all_pages complete~ total entries synced: {total_so_far}")
                break

            page += 1

    await load_fuzzy_cache()


async def sync_latest_once():
    """
    Fetch the sync_latest endpoint and upsert all returned entries.
    Refreshes fuzzy cache after a successful sync.
    """
    try:
        async with aiohttp.ClientSession(headers=_HEADERS) as session:
            try:
                async with session.get(
                    _SYNC_LATEST_URL,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 429:
                        log.warning("sync_latest — rate limited, waiting 5s then retrying~")
                        await asyncio.sleep(5)
                        async with session.get(
                            _SYNC_LATEST_URL,
                            timeout=aiohttp.ClientTimeout(total=30)
                        ) as retry_resp:
                            if retry_resp.status != 200:
                                log.warning(f"sync_latest retry failed with status {retry_resp.status}~")
                                return
                            data = await retry_resp.json()
                    elif resp.status != 200:
                        log.warning(f"sync_latest — unexpected status {resp.status}~")
                        return
                    else:
                        data = await resp.json()

            except Exception as e:
                log.warning(f"sync_latest fetch error: {e}")
                return

        entries = data.get("data", [])
        for entry in entries:
            await upsert_anime(entry)

        if entries:
            log.info(f"sync_latest_once — upserted {len(entries)} entries~")

        await load_fuzzy_cache()

    except Exception as e:
        log.warning(f"sync_latest_once outer error: {e}")
