import random
import math
from functions import database_functions as db

# XP Settings
XP_PER_MESSAGE_MIN = 15
XP_PER_MESSAGE_MAX = 25
XP_COOLDOWN_SECONDS = 60  # Prevent XP farming


def xp_for_level(level: int) -> int:
    """Calculate the total XP needed to reach a given level."""
    return 5 * (level ** 2) + 50 * level + 100


def level_from_xp(xp: int) -> int:
    """Calculate the level from total XP."""
    level = 0
    remaining = xp
    while remaining >= xp_for_level(level):
        remaining -= xp_for_level(level)
        level += 1
    return level


def xp_progress(xp: int, level: int) -> tuple[int, int]:
    """Return (current_xp_in_level, xp_needed_for_next_level)."""
    total_xp_for_current_level = sum(xp_for_level(l) for l in range(level))
    current_xp_in_level = xp - total_xp_for_current_level
    needed = xp_for_level(level)
    return current_xp_in_level, needed


def progress_bar(current: int, total: int, length: int = 10) -> str:
    """Generate a text-based progress bar."""
    filled = int(length * current / total) if total > 0 else 0
    bar = "█" * filled + "░" * (length - filled)
    return bar


async def process_message_xp(guild_id: int, user_id: int) -> tuple[bool, int]:
    """
    Process XP gain for a message. Returns (leveled_up, new_level).
    Respects cooldown to prevent XP farming.
    """
    import time

    data = await db.get_user_level(guild_id, user_id)
    now = int(time.time())

    # Cooldown check
    if now - data["last_xp_time"] < XP_COOLDOWN_SECONDS:
        return False, data["level"]

    # Award random XP
    xp_gain = random.randint(XP_PER_MESSAGE_MIN, XP_PER_MESSAGE_MAX)
    new_xp = data["xp"] + xp_gain
    old_level = data["level"]
    new_level = level_from_xp(new_xp)

    await db.update_user_xp(guild_id, user_id, new_xp, new_level)

    leveled_up = new_level > old_level
    return leveled_up, new_level


async def get_rank(guild_id: int, user_id: int) -> int:
    """Get user's rank position on the leaderboard (1-indexed)."""
    leaderboard = await db.get_leaderboard(guild_id, limit=9999)
    for i, entry in enumerate(leaderboard, start=1):
        if entry["user_id"] == user_id:
            return i
    return 0
