import aiosqlite
import time

DB_PATH = "assets/database.db"


# ── Schema Initialization ──────────────────────────────────────────────────

async def initialize_database():
    """Create all tables if they don't exist. Called once on bot startup."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS guild_config (
                guild_id INTEGER PRIMARY KEY,
                welcome_channel_id INTEGER,
                welcome_message TEXT DEFAULT 'Welcome to the server, {user}!',
                leave_channel_id INTEGER,
                leave_message TEXT DEFAULT 'Goodbye, {user}!',
                log_channel_id INTEGER,
                mod_log_channel_id INTEGER,
                starboard_channel_id INTEGER,
                starboard_threshold INTEGER DEFAULT 3,
                starboard_emoji TEXT DEFAULT '⭐',
                level_channel_id INTEGER,
                level_enabled INTEGER DEFAULT 0,
                automod_enabled INTEGER DEFAULT 0,
                automod_anti_spam INTEGER DEFAULT 0,
                automod_anti_invite INTEGER DEFAULT 0,
                automod_anti_massmention INTEGER DEFAULT 0,
                automod_massmention_threshold INTEGER DEFAULT 5,
                ticket_category_id INTEGER,
                ticket_log_channel_id INTEGER,
                autorole_id INTEGER
            );

            CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                moderator_id INTEGER NOT NULL,
                reason TEXT NOT NULL,
                timestamp INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS mod_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                moderator_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                reason TEXT,
                duration TEXT,
                timestamp INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS user_messages (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                message_count INTEGER DEFAULT 0,
                PRIMARY KEY (guild_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS levels (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 0,
                last_xp_time INTEGER DEFAULT 0,
                PRIMARY KEY (guild_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS level_roles (
                guild_id INTEGER NOT NULL,
                level INTEGER NOT NULL,
                role_id INTEGER NOT NULL,
                PRIMARY KEY (guild_id, level)
            );

            CREATE TABLE IF NOT EXISTS autoroles (
                guild_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL,
                PRIMARY KEY (guild_id, role_id)
            );

            CREATE TABLE IF NOT EXISTS custom_commands (
                guild_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                response TEXT NOT NULL,
                creator_id INTEGER NOT NULL,
                created_at INTEGER NOT NULL,
                PRIMARY KEY (guild_id, name)
            );

            CREATE TABLE IF NOT EXISTS starboard (
                guild_id INTEGER NOT NULL,
                original_message_id INTEGER NOT NULL,
                starboard_message_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                author_id INTEGER NOT NULL,
                star_count INTEGER DEFAULT 0,
                PRIMARY KEY (guild_id, original_message_id)
            );

            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                guild_id INTEGER,
                message TEXT NOT NULL,
                remind_at INTEGER NOT NULL,
                created_at INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                status TEXT DEFAULT 'open',
                created_at INTEGER NOT NULL,
                closed_at INTEGER
            );

            CREATE TABLE IF NOT EXISTS giveaways (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                host_id INTEGER NOT NULL,
                prize TEXT NOT NULL,
                winners INTEGER DEFAULT 1,
                end_time INTEGER NOT NULL,
                ended INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS temp_bans (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                moderator_id INTEGER NOT NULL,
                reason TEXT,
                unban_at INTEGER NOT NULL,
                PRIMARY KEY (guild_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS afk (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                reason TEXT DEFAULT 'AFK',
                timestamp INTEGER NOT NULL,
                PRIMARY KEY (guild_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS automod_badwords (
                guild_id INTEGER NOT NULL,
                word TEXT NOT NULL,
                PRIMARY KEY (guild_id, word)
            );

            CREATE TABLE IF NOT EXISTS reaction_roles (
                guild_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                emoji TEXT NOT NULL,
                role_id INTEGER NOT NULL,
                PRIMARY KEY (guild_id, message_id, emoji)
            );

            CREATE TABLE IF NOT EXISTS self_roles (
                guild_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL,
                PRIMARY KEY (guild_id, role_id)
            );
        """)
        await db.commit()


# ── Guild Config ───────────────────────────────────────────────────────────

async def get_guild_config(guild_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM guild_config WHERE guild_id = ?", (guild_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def ensure_guild_config(guild_id: int):
    """Insert a default config row for a guild if it doesn't exist."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO guild_config (guild_id) VALUES (?)", (guild_id,)
        )
        await db.commit()


async def update_guild_config(guild_id: int, **kwargs):
    """Update specific guild config fields. Pass column=value keyword args."""
    if not kwargs:
        return
    await ensure_guild_config(guild_id)
    columns = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [guild_id]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"UPDATE guild_config SET {columns} WHERE guild_id = ?", values
        )
        await db.commit()


# ── Warnings ───────────────────────────────────────────────────────────────

async def add_warning(guild_id: int, user_id: int, moderator_id: int, reason: str) -> int:
    """Add a warning and return the warning ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO warnings (guild_id, user_id, moderator_id, reason, timestamp) VALUES (?, ?, ?, ?, ?)",
            (guild_id, user_id, moderator_id, reason, int(time.time()))
        )
        await db.commit()
        return cursor.lastrowid  # type: ignore


async def get_warnings(guild_id: int, user_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM warnings WHERE guild_id = ? AND user_id = ? ORDER BY timestamp DESC",
            (guild_id, user_id)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def delete_warning(warning_id: int, guild_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM warnings WHERE id = ? AND guild_id = ?", (warning_id, guild_id)
        )
        await db.commit()
        return cursor.rowcount > 0  # type: ignore


async def clear_warnings(guild_id: int, user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM warnings WHERE guild_id = ? AND user_id = ?", (guild_id, user_id)
        )
        await db.commit()
        return cursor.rowcount  # type: ignore


# ── Mod Actions ────────────────────────────────────────────────────────────

async def log_mod_action(guild_id: int, user_id: int, moderator_id: int, action: str, reason: str | None = None, duration: str | None = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO mod_actions (guild_id, user_id, moderator_id, action, reason, duration, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (guild_id, user_id, moderator_id, action, reason, duration, int(time.time()))
        )
        await db.commit()


async def get_mod_actions(guild_id: int, user_id: int, limit: int = 10) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM mod_actions WHERE guild_id = ? AND user_id = ? ORDER BY timestamp DESC LIMIT ?",
            (guild_id, user_id, limit)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


# ── User Messages ──────────────────────────────────────────────────────────

async def record_user_messages(user_id: int, guild_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO user_messages (guild_id, user_id, message_count) VALUES (?, ?, 1) "
            "ON CONFLICT(guild_id, user_id) DO UPDATE SET message_count = message_count + 1",
            (guild_id, user_id)
        )
        await db.commit()


async def read_user_messages(user_id: int, guild_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT message_count FROM user_messages WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id)
        )
        row = await cursor.fetchone()
        return row[0] if row else 0


# ── Levels / XP ───────────────────────────────────────────────────────────

async def get_user_level(guild_id: int, user_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM levels WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id)
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return {"guild_id": guild_id, "user_id": user_id, "xp": 0, "level": 0, "last_xp_time": 0}


async def update_user_xp(guild_id: int, user_id: int, xp: int, level: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO levels (guild_id, user_id, xp, level, last_xp_time) VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(guild_id, user_id) DO UPDATE SET xp = ?, level = ?, last_xp_time = ?",
            (guild_id, user_id, xp, level, int(time.time()), xp, level, int(time.time()))
        )
        await db.commit()


async def get_leaderboard(guild_id: int, limit: int = 10) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM levels WHERE guild_id = ? ORDER BY level DESC, xp DESC LIMIT ?",
            (guild_id, limit)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_level_roles(guild_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM level_roles WHERE guild_id = ? ORDER BY level ASC", (guild_id,)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def set_level_role(guild_id: int, level: int, role_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO level_roles (guild_id, level, role_id) VALUES (?, ?, ?)",
            (guild_id, level, role_id)
        )
        await db.commit()


async def remove_level_role(guild_id: int, level: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM level_roles WHERE guild_id = ? AND level = ?", (guild_id, level)
        )
        await db.commit()


# ── Custom Commands ────────────────────────────────────────────────────────

async def add_custom_command(guild_id: int, name: str, response: str, creator_id: int) -> bool:
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO custom_commands (guild_id, name, response, creator_id, created_at) VALUES (?, ?, ?, ?, ?)",
                (guild_id, name.lower(), response, creator_id, int(time.time()))
            )
            await db.commit()
            return True
    except aiosqlite.IntegrityError:
        return False


async def remove_custom_command(guild_id: int, name: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM custom_commands WHERE guild_id = ? AND name = ?",
            (guild_id, name.lower())
        )
        await db.commit()
        return cursor.rowcount > 0  # type: ignore


async def get_custom_command(guild_id: int, name: str) -> str | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT response FROM custom_commands WHERE guild_id = ? AND name = ?",
            (guild_id, name.lower())
        )
        row = await cursor.fetchone()
        return row[0] if row else None


async def get_all_custom_commands(guild_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM custom_commands WHERE guild_id = ? ORDER BY name", (guild_id,)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


# ── Starboard ──────────────────────────────────────────────────────────────

async def get_starboard_entry(guild_id: int, original_message_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM starboard WHERE guild_id = ? AND original_message_id = ?",
            (guild_id, original_message_id)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def upsert_starboard_entry(guild_id: int, original_message_id: int, starboard_message_id: int, channel_id: int, author_id: int, star_count: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO starboard (guild_id, original_message_id, starboard_message_id, channel_id, author_id, star_count) "
            "VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(guild_id, original_message_id) DO UPDATE SET star_count = ?, starboard_message_id = ?",
            (guild_id, original_message_id, starboard_message_id, channel_id, author_id, star_count, star_count, starboard_message_id)
        )
        await db.commit()


async def delete_starboard_entry(guild_id: int, original_message_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM starboard WHERE guild_id = ? AND original_message_id = ?",
            (guild_id, original_message_id)
        )
        await db.commit()


# ── Reminders ──────────────────────────────────────────────────────────────

async def add_reminder(user_id: int, channel_id: int, guild_id: int | None, message: str, remind_at: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO reminders (user_id, channel_id, guild_id, message, remind_at, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, channel_id, guild_id, message, remind_at, int(time.time()))
        )
        await db.commit()
        return cursor.lastrowid  # type: ignore


async def get_due_reminders() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM reminders WHERE remind_at <= ?", (int(time.time()),)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def delete_reminder(reminder_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
        await db.commit()


async def get_user_reminders(user_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM reminders WHERE user_id = ? ORDER BY remind_at ASC", (user_id,)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


# ── Tickets ────────────────────────────────────────────────────────────────

async def create_ticket(guild_id: int, channel_id: int, user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO tickets (guild_id, channel_id, user_id, created_at) VALUES (?, ?, ?, ?)",
            (guild_id, channel_id, user_id, int(time.time()))
        )
        await db.commit()
        return cursor.lastrowid  # type: ignore


async def close_ticket(channel_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE tickets SET status = 'closed', closed_at = ? WHERE channel_id = ? AND status = 'open'",
            (int(time.time()), channel_id)
        )
        await db.commit()


async def get_ticket(channel_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM tickets WHERE channel_id = ? AND status = 'open'", (channel_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_user_open_tickets(guild_id: int, user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM tickets WHERE guild_id = ? AND user_id = ? AND status = 'open'",
            (guild_id, user_id)
        )
        row = await cursor.fetchone()
        return row[0] if row else 0


# ── Giveaways ──────────────────────────────────────────────────────────────

async def create_giveaway(guild_id: int, channel_id: int, message_id: int, host_id: int, prize: str, winners: int, end_time: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO giveaways (guild_id, channel_id, message_id, host_id, prize, winners, end_time) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (guild_id, channel_id, message_id, host_id, prize, winners, end_time)
        )
        await db.commit()
        return cursor.lastrowid  # type: ignore


async def get_active_giveaways() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM giveaways WHERE ended = 0 AND end_time <= ?", (int(time.time()),)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def end_giveaway(giveaway_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE giveaways SET ended = 1 WHERE id = ?", (giveaway_id,)
        )
        await db.commit()


async def get_giveaway_by_message(message_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM giveaways WHERE message_id = ?", (message_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


# ── Temp Bans ──────────────────────────────────────────────────────────────

async def add_temp_ban(guild_id: int, user_id: int, moderator_id: int, reason: str | None, unban_at: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO temp_bans (guild_id, user_id, moderator_id, reason, unban_at) VALUES (?, ?, ?, ?, ?)",
            (guild_id, user_id, moderator_id, reason, unban_at)
        )
        await db.commit()


async def get_expired_temp_bans() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM temp_bans WHERE unban_at <= ?", (int(time.time()),)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def remove_temp_ban(guild_id: int, user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM temp_bans WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id)
        )
        await db.commit()


# ── AFK ────────────────────────────────────────────────────────────────────

async def set_afk(guild_id: int, user_id: int, reason: str = "AFK"):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO afk (guild_id, user_id, reason, timestamp) VALUES (?, ?, ?, ?)",
            (guild_id, user_id, reason, int(time.time()))
        )
        await db.commit()


async def get_afk(guild_id: int, user_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM afk WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def remove_afk(guild_id: int, user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM afk WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id)
        )
        await db.commit()
        return cursor.rowcount > 0  # type: ignore


# ── Automod Badwords ───────────────────────────────────────────────────────

async def add_badword(guild_id: int, word: str) -> bool:
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO automod_badwords (guild_id, word) VALUES (?, ?)",
                (guild_id, word.lower())
            )
            await db.commit()
            return True
    except aiosqlite.IntegrityError:
        return False


async def remove_badword(guild_id: int, word: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM automod_badwords WHERE guild_id = ? AND word = ?",
            (guild_id, word.lower())
        )
        await db.commit()
        return cursor.rowcount > 0  # type: ignore


async def get_badwords(guild_id: int) -> list[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT word FROM automod_badwords WHERE guild_id = ?", (guild_id,)
        )
        rows = await cursor.fetchall()
        return [r[0] for r in rows]


# ── Reaction Roles ─────────────────────────────────────────────────────────

async def add_reaction_role(guild_id: int, message_id: int, emoji: str, role_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO reaction_roles (guild_id, message_id, emoji, role_id) VALUES (?, ?, ?, ?)",
            (guild_id, message_id, emoji, role_id)
        )
        await db.commit()


async def get_reaction_role(guild_id: int, message_id: int, emoji: str) -> int | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT role_id FROM reaction_roles WHERE guild_id = ? AND message_id = ? AND emoji = ?",
            (guild_id, message_id, emoji)
        )
        row = await cursor.fetchone()
        return row[0] if row else None


async def remove_reaction_role(guild_id: int, message_id: int, emoji: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM reaction_roles WHERE guild_id = ? AND message_id = ? AND emoji = ?",
            (guild_id, message_id, emoji)
        )
        await db.commit()
        return cursor.rowcount > 0  # type: ignore


async def get_all_reaction_roles(guild_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM reaction_roles WHERE guild_id = ?", (guild_id,)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


# ── Self Roles ─────────────────────────────────────────────────────────────

async def add_self_role(guild_id: int, role_id: int) -> bool:
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO self_roles (guild_id, role_id) VALUES (?, ?)",
                (guild_id, role_id)
            )
            await db.commit()
            return True
    except aiosqlite.IntegrityError:
        return False


async def remove_self_role(guild_id: int, role_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM self_roles WHERE guild_id = ? AND role_id = ?",
            (guild_id, role_id)
        )
        await db.commit()
        return cursor.rowcount > 0  # type: ignore


async def get_self_roles(guild_id: int) -> list[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT role_id FROM self_roles WHERE guild_id = ?", (guild_id,)
        )
        rows = await cursor.fetchall()
        return [r[0] for r in rows]