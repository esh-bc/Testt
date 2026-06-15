# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   api.py — AnimeTadka + TMDB + Jikan combined fetcher
#   © AnimeTadka
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import re
import aiohttp
import asyncio
from config import (
    SEARCH_API_URL, SEARCH_API_USER_AGENT,
    TMDB_API_KEY, TMDB_BASE_URL, TMDB_IMAGE_BASE
)

TYPE_ICONS = {
    "tv":      "◈ TV Series",
    "movie":   "◇ Movie",
    "ova":     "▸ OVA",
    "ona":     "▸ ONA",
    "special": "✦ Special",
}

# Regex to pull TMDB ID out of a full TMDB URL
# e.g. https://www.themoviedb.org/tv/12345  or  /movie/67890
_TMDB_URL_RE = re.compile(r'/(?:tv|movie)/(\d+)', re.IGNORECASE)

_JIKAN_BASE = "https://api.jikan.moe/v4"
_BOT_UA     = "YukiBot/1.0"


# ── AnimeTadka Search ─────────────────────────────

async def search_anime(query: str) -> list[dict] | None:
    if len(query.strip()) < 3:
        return []
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                SEARCH_API_URL,
                params={"q": query},
                headers={"User-Agent": SEARCH_API_USER_AGENT},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("data", [])
                elif resp.status == 429:
                    return None
                elif resp.status == 400:
                    return []
                else:
                    return None
    except Exception:
        return None


# ── Jikan Fallback ────────────────────────────────

async def search_jikan(query: str) -> dict | None:
    """
    GET https://api.jikan.moe/v4/anime?q=<query>&limit=1
    Returns { title, mal_id } if a result exists, else None.
    Timeout: 8 seconds.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{_JIKAN_BASE}/anime",
                params={"q": query, "limit": 1},
                headers={"User-Agent": _BOT_UA},
                timeout=aiohttp.ClientTimeout(total=8)
            ) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                items = data.get("data", [])
                if not items:
                    return None
                item = items[0]
                return {
                    "title":  item.get("title", ""),
                    "mal_id": item.get("mal_id", ""),
                }
    except Exception:
        return None


# ── TMDB ID extraction helpers ────────────────────

def _extract_tmdb_id_from_result(at_result: dict) -> tuple[str, str]:
    """
    Pull tmdb_id and media_type from an AnimeTadka result dict.
    Handles:
      - at_result["tmdb_id"]   (direct numeric ID or string ID)
      - at_result["tmdb_link"] / at_result["tmdb_url"]  (full TMDB URL)
    Returns (tmdb_id_str, guessed_media_type).
    """
    anime_type = at_result.get("type", "tv").lower()
    media_type = "movie" if anime_type in ("movie", "film") else "tv"

    # 1. Direct tmdb_id field
    tmdb_id = str(at_result.get("tmdb_id", "")).strip()
    if tmdb_id and tmdb_id != "None":
        return tmdb_id, media_type

    # 2. tmdb_link / tmdb_url field (full URL)
    for field in ("tmdb_link", "tmdb_url", "tmdb"):
        url_val = str(at_result.get(field, "")).strip()
        if url_val:
            # Also check if the URL contains /movie/ to set media_type
            if "/movie/" in url_val.lower():
                media_type = "movie"
            elif "/tv/" in url_val.lower():
                media_type = "tv"
            m = _TMDB_URL_RE.search(url_val)
            if m:
                return m.group(1), media_type

    return "", media_type


# ── TMDB Fetch ────────────────────────────────────

async def fetch_tmdb_data(tmdb_id: str, media_type: str = "tv") -> dict | None:
    """
    Fetches full TMDB data for a given tmdb_id.
    Uses media_type hint first; falls back to the other type if not found.
    """
    if not tmdb_id:
        return None

    async with aiohttp.ClientSession() as session:
        result = await _tmdb_fetch(session, tmdb_id, media_type)
        if not result:
            fallback = "movie" if media_type == "tv" else "tv"
            result   = await _tmdb_fetch(session, tmdb_id, fallback)
        return result


async def _tmdb_fetch(session: aiohttp.ClientSession, tmdb_id: str, media_type: str) -> dict | None:
    try:
        url    = f"{TMDB_BASE_URL}/{media_type}/{tmdb_id}"
        params = {
            "api_key":            TMDB_API_KEY,
            "append_to_response": "credits,keywords"
        }
        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=8)) as resp:
            if resp.status == 200:
                data = await resp.json()
                return _parse_tmdb(data, media_type)
            return None
    except Exception:
        return None


def _parse_tmdb(data: dict, media_type: str) -> dict:
    """Extract everything useful from TMDB response."""

    poster   = f"{TMDB_IMAGE_BASE}{data['poster_path']}"   if data.get("poster_path")   else None
    backdrop = f"{TMDB_IMAGE_BASE}{data['backdrop_path']}" if data.get("backdrop_path") else None

    title    = data.get("name") or data.get("title") or "Unknown"
    overview = data.get("overview") or ""
    if len(overview) > 300:
        overview = overview[:297] + "..."

    genres   = [g["name"] for g in data.get("genres", [])]
    rating   = data.get("vote_average", 0)
    votes    = data.get("vote_count", 0)
    rating_str = f"{rating:.1f} ✦ ({votes:,} votes)" if rating else None

    release  = data.get("first_air_date") or data.get("release_date") or ""
    year     = release[:4] if release else None

    episodes = data.get("number_of_episodes")
    seasons  = data.get("number_of_seasons")

    runtime  = None
    if media_type == "movie":
        rt = data.get("runtime")
        if rt:
            runtime = f"{rt} min"
    else:
        ep_rt = data.get("episode_run_time", [])
        if ep_rt:
            runtime = f"~{ep_rt[0]} min / ep"

    status    = data.get("status") or ""
    countries = data.get("origin_country") or []
    country   = ", ".join(countries) if countries else None

    cast = []
    for member in data.get("credits", {}).get("cast", [])[:5]:
        name = member.get("name", "")
        if name:
            cast.append(name)

    keywords = []
    kw_data  = data.get("keywords", {})
    kw_list  = kw_data.get("results") or kw_data.get("keywords") or []
    for kw in kw_list[:6]:
        name = kw.get("name", "")
        if name:
            keywords.append(name)

    popularity = data.get("popularity")

    return {
        "tmdb_title": title,
        "poster":     poster,
        "backdrop":   backdrop,
        "overview":   overview,
        "genres":     genres,
        "rating":     rating_str,
        "year":       year,
        "episodes":   episodes,
        "seasons":    seasons,
        "runtime":    runtime,
        "status":     status,
        "country":    country,
        "cast":       cast,
        "keywords":   keywords,
        "popularity": popularity,
        "media_type": media_type,
    }


# ── Combine both sources ──────────────────────────

async def get_full_anime_data(at_result: dict) -> dict:
    """
    Takes one AnimeTadka result dict, fetches TMDB data using
    the tmdb_id or tmdb_link from AnimeTadka, merges everything.
    """
    tmdb_id, media_type = _extract_tmdb_id_from_result(at_result)
    tmdb = await fetch_tmdb_data(tmdb_id, media_type) if tmdb_id else None

    combined = {
        # From AnimeTadka
        "title":     at_result.get("title", "Unknown"),
        "type":      format_type(at_result.get("type", "")),
        "studio":    at_result.get("studio", ""),
        "languages": format_languages(at_result.get("languages", [])),
        "watch_url": at_result.get("url", ""),
        "mal_id":    at_result.get("mal_id", ""),
        "tmdb_id":   tmdb_id,

        # From TMDB (with fallbacks)
        "poster":    tmdb.get("poster")    if tmdb else None,
        "backdrop":  tmdb.get("backdrop")  if tmdb else None,
        "overview":  tmdb.get("overview")  if tmdb else "",
        "genres":    tmdb.get("genres")    if tmdb else [],
        "rating":    tmdb.get("rating")    if tmdb else None,
        "year":      tmdb.get("year")      if tmdb else None,
        "episodes":  tmdb.get("episodes")  if tmdb else None,
        "seasons":   tmdb.get("seasons")   if tmdb else None,
        "runtime":   tmdb.get("runtime")   if tmdb else None,
        "status":    tmdb.get("status")    if tmdb else None,
        "country":   tmdb.get("country")   if tmdb else None,
        "cast":      tmdb.get("cast")      if tmdb else [],
        "keywords":  tmdb.get("keywords")  if tmdb else [],
    }
    return combined


async def enrich_results(results: list[dict]) -> list[dict]:
    """Enrich all results concurrently."""
    tasks = [get_full_anime_data(r) for r in results]
    return await asyncio.gather(*tasks)


# ── Formatters ────────────────────────────────────

def format_languages(langs: list[str]) -> str:
    cleaned = []
    for lang in langs:
        name = lang.strip().title()
        if name and name not in cleaned:
            cleaned.append(name)
    return ", ".join(cleaned) if cleaned else "Unknown"


def format_type(type_str: str) -> str:
    return TYPE_ICONS.get(type_str.lower(), f"◈ {type_str.title()}")
