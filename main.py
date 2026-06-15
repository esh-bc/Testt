# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   main.py — YukiBot Entry Point
#   Built for AnimeTadka
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN, OWNER_ID, RESET_DB
from utils import state, db
from utils.auto_delete import auto_delete_loop
from utils.sync import sync_all_pages, sync_latest_once
from handlers import auth, admin, general, listener

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
log = logging.getLogger("YukiBot")


async def cron_loop():
    """Run sync_latest_once every 2 hours in the background."""
    while True:
        await asyncio.sleep(7200)
        await sync_latest_once()


async def on_startup(bot: Bot):
    log.info("YukiBot starting~")

    try:
        groups = await db.get_authorised_groups()
        for gid in groups:
            state.authorise_group_memory(gid)
        log.info(f"Loaded {len(groups)} authorised groups")
    except Exception as e:
        log.warning(f"Could not load groups from DB: {e}")
        groups = set()

    try:
        admins = await db.get_all_admins()
        for uid in admins:
            state.add_bot_admin_memory(uid)
        log.info(f"Loaded {len(admins)} admins")
    except Exception as e:
        log.warning(f"Could not load admins from DB: {e}")
        admins = set()

    # ── Anime index seed / cache load ──────────────
    try:
        if RESET_DB:
            log.info("RESET_DB=true~ dropping anime_index and re-syncing~")
            await db.drop_anime_index()

        count = await db.get_anime_count()
        if count == 0:
            log.info("Anime index empty~ starting full sync~")
            await sync_all_pages()
        else:
            log.info(f"Anime index already seeded, skipping sync_all~ ({count} entries in DB)")
            await db.load_fuzzy_cache()
    except Exception as e:
        log.warning(f"Anime index startup error: {e}")

    # ── Background loops ───────────────────────────
    asyncio.create_task(auto_delete_loop(bot))
    log.info("Auto-delete loop scheduled~")

    asyncio.create_task(cron_loop())
    log.info("Cron loop scheduled~ (sync_latest every 2h)~")

    try:
        await bot.send_message(
            OWNER_ID,
            (
                "✦ ara ara~ yuki is online~\n"
                "◈ all systems ready~\n"
                f"◇ {len(groups)} groups loaded~\n"
                f"✦ {len(admins)} admins loaded~\n"
                "◈ auto-delete is active~\n"
                "◇ anime index is hot and ready~"
            )
        )
    except Exception:
        log.info("Could not notify owner — start a chat with the bot first~")

    log.info("YukiBot ready~")


async def on_shutdown(bot: Bot):
    log.info("YukiBot shutting down~")
    try:
        await bot.send_message(
            OWNER_ID,
            "◈ mou~ yuki is going offline~\n✦ see you soon~"
        )
    except Exception:
        pass


async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher()

    dp.include_router(general.router)
    dp.include_router(auth.router)
    dp.include_router(admin.router)
    dp.include_router(listener.router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    log.info("Starting polling~")
    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types()
    )


if __name__ == "__main__":
    asyncio.run(main())
