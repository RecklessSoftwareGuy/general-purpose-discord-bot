import aiosqlite

async def create_guild_tables(guildId: int):
    async with aiosqlite.connect("assets/database.db") as db:
        await db.execute(f"CREATE TABLE IF NOT EXISTS {guildId} (userId INTEGER, count)")