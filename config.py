# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   YukiBot — Built for AnimeTadka
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import os
BOT_TOKEN = os.environ["BOT_TOKEN"]

# Owner Telegram numeric ID
OWNER_ID = 8264404281

# Private log channel ID (must start with -100...)
LOG_CHANNEL_ID = -1008264404281  # ← replace with your real channel ID

# MongoDB
MONGO_URI = "mongodb+srv://singhyashraj:leechbotxesh@cluster0.i1ruod.mongodb.net/?appName=Cluster0"
MONGO_DB   = "yukibot"

# AnimeTadka Search API
SEARCH_API_URL        = "https://animetadka.com/at-search"
SEARCH_API_USER_AGENT = "YukiBot/1.0"

# TMDB API
TMDB_API_KEY    = "1cf9edb8dca6517ff5c3d8930bb77d6e"
TMDB_BASE_URL   = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

# Rate limiting — per user in a group
RATE_LIMIT_REQUESTS = 3   # max searches
RATE_LIMIT_WINDOW   = 30  # per N seconds

# Pagination — results per page in search list
PAGE_SIZE = 5

# Auto-delete delay in seconds (10 minutes)
AUTO_DELETE_DELAY = 600

# Bot meta
CREDIT_LINE = "© AnimeTadka"

# Drop and re-sync anime_index on next startup when set to "true"
RESET_DB = os.environ.get("RESET_DB", "false").lower() == "true"
