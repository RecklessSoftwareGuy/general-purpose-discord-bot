import aiosqlite

async def create_guild_tables(guildId: int):
    async with aiosqlite.connect("assets/database.db") as db:
        await db.execute(f"CREATE TABLE IF NOT EXISTS {guildId} (userId INTEGER PRIMARY KEY, nWarns INTEGER, warnings TEXT, nMutes INTEGER, mutes TEXT, nKicks INTEGER, kicks INTEGER, nBans INTEGER, bans TEXT, nMessages INTEGER)")
        await db.commit()
        await db.close()

async def read_user_messages(userId: int, guildId: int):
    async with aiosqlite.connect("assets/database.db") as db:
        cursor = await db.execute(f"SELECT nMessages FROM {guildId} WHERE userId = {userId}")
        nMessages = await cursor.fetchone()
        await db.close()
    if nMessages: return nMessages[0]
    return 0

async def record_user_messages(userId: int, guildId: int):
    async with aiosqlite.connect("assets/database.db") as db:
        # cursor = await db.execute(f"SELECT nMessages FROM {guildId} WHERE userId = {userId}")
        # nmessages = await cursor.fetchone()
        # if nmessages is None:
        #     nmessages = [0]
        # nMessages = nmessages[0]
        await db.execute(f"UPDATE {guildId} SET nMessages = nMessages + 1 WHERE userId = {userId}")
        await db.commit()
        await db.close()