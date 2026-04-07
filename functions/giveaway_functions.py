import discord
import random
from functions import database_functions as db


async def pick_winners(channel: discord.TextChannel, message_id: int, winner_count: int) -> list[discord.Member]:
    """Pick random winners from a giveaway message's reactions."""
    try:
        message = await channel.fetch_message(message_id)
    except (discord.NotFound, discord.HTTPException):
        return []

    # Find the 🎉 reaction
    reaction = None
    for r in message.reactions:
        if str(r.emoji) == "🎉":
            reaction = r
            break

    if not reaction:
        return []

    users = []
    async for user in reaction.users():
        if not user.bot:
            member = channel.guild.get_member(user.id)
            if member:
                users.append(member)

    if not users:
        return []

    winners = random.sample(users, min(winner_count, len(users)))
    return winners


async def end_giveaway_flow(bot, giveaway: dict) -> tuple[list[discord.Member], discord.Message | None]:
    """
    End a giveaway: pick winners, update DB, edit the message.
    Returns (winners, message).
    """
    guild = bot.get_guild(giveaway["guild_id"])
    if not guild:
        await db.end_giveaway(giveaway["id"])
        return [], None

    channel = guild.get_channel(giveaway["channel_id"])
    if not channel or not isinstance(channel, discord.TextChannel):
        await db.end_giveaway(giveaway["id"])
        return [], None

    winners = await pick_winners(channel, giveaway["message_id"], giveaway["winners"])
    await db.end_giveaway(giveaway["id"])

    try:
        message = await channel.fetch_message(giveaway["message_id"])
    except (discord.NotFound, discord.HTTPException):
        return winners, None

    if winners:
        winner_text = ", ".join(w.mention for w in winners)
        em = discord.Embed(
            title="🎉 Giveaway Ended!",
            description=f"**Prize:** {giveaway['prize']}\n**Winner(s):** {winner_text}",
            colour=discord.Colour.gold(),
            timestamp=discord.utils.utcnow()
        )
    else:
        em = discord.Embed(
            title="🎉 Giveaway Ended!",
            description=f"**Prize:** {giveaway['prize']}\n**Winner(s):** No valid entries!",
            colour=discord.Colour.dark_grey(),
            timestamp=discord.utils.utcnow()
        )

    em.set_footer(text=f"Hosted by user ID {giveaway['host_id']}")

    try:
        await message.edit(embed=em)
    except discord.HTTPException:
        pass

    return winners, message
