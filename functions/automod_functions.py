import time
import re
from collections import defaultdict
from functions import database_functions as db

# In-memory spam tracking (resets on bot restart, which is fine)
_message_cache: dict[int, list[tuple[int, float]]] = defaultdict(list)  # user_id -> [(guild_id, timestamp)]
SPAM_THRESHOLD = 5   # messages
SPAM_WINDOW = 5.0    # seconds

# Discord invite regex
INVITE_PATTERN = re.compile(
    r"(discord\.gg|discord\.com/invite|discordapp\.com/invite)/[\w-]+",
    re.IGNORECASE
)

# Mass mention threshold is configurable per guild; default 5
DEFAULT_MASS_MENTION_THRESHOLD = 5


def check_spam(user_id: int, guild_id: int) -> bool:
    """
    Check if a user is spamming. Returns True if spam detected.
    Tracks timestamps in memory.
    """
    now = time.time()
    key = user_id

    # Clean old entries
    _message_cache[key] = [
        (gid, ts) for gid, ts in _message_cache[key]
        if ts > now - SPAM_WINDOW and gid == guild_id
    ]

    _message_cache[key].append((guild_id, now))

    return len(_message_cache[key]) >= SPAM_THRESHOLD


def check_invite_link(content: str) -> bool:
    """Check if a message contains a Discord invite link."""
    return bool(INVITE_PATTERN.search(content))


def check_mass_mention(content: str, mentions_count: int, threshold: int = DEFAULT_MASS_MENTION_THRESHOLD) -> bool:
    """Check if a message has too many mentions."""
    return mentions_count >= threshold


def check_badwords(content: str, badwords: list[str]) -> bool:
    """Check if a message contains any bad words."""
    lower = content.lower()
    return any(word in lower for word in badwords)


async def get_automod_config(guild_id: int) -> dict:
    """Get automod configuration for a guild."""
    config = await db.get_guild_config(guild_id)
    if not config:
        return {
            "enabled": False,
            "anti_spam": False,
            "anti_invite": False,
            "anti_massmention": False,
            "massmention_threshold": DEFAULT_MASS_MENTION_THRESHOLD,
        }
    return {
        "enabled": bool(config.get("automod_enabled", 0)),
        "anti_spam": bool(config.get("automod_anti_spam", 0)),
        "anti_invite": bool(config.get("automod_anti_invite", 0)),
        "anti_massmention": bool(config.get("automod_anti_massmention", 0)),
        "massmention_threshold": config.get("automod_massmention_threshold", DEFAULT_MASS_MENTION_THRESHOLD),
    }


def clear_spam_cache(user_id: int):
    """Clear spam cache for a user."""
    _message_cache.pop(user_id, None)
