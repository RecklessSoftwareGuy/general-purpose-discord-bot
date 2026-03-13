import discord

def muted_x0(user: discord.Member | discord.User, duration: int) -> discord.Embed:
    em = discord.Embed(description=f"`{user.name}` was muted for {duration} hours.", color=discord.Colour.green())
    return em

def muted_dm_x1(moderator: discord.User | discord.Member, duration: int, reason: str) -> discord.Embed:
    em = discord.Embed(title="You have been muted", description=f"Muted by {moderator.mention} for {duration} hours.\n`Reason: ` {reason}",  color=discord.Colour.green())
    return em

def kick_x0(user: discord.Member | discord.User, reason: str) -> discord.Embed:
    em = discord.Embed(description=f"Kicked {user.name}", color=discord.Colour.green())
    return em

def kick_dm_x1(moderator: discord.Member | discord.User, reason: str, guildName: str) -> discord.Embed:
    em = discord.Embed(title=f"You have been kicked from {guildName}", description=f"`Reason: ` {reason}")
    em.set_footer(text=f"Kicked by {moderator.name}")
    return em

def ban_x0(user: discord.Member | discord.User) -> discord.Embed:
    em = discord.Embed(description=f"Banned {user.name}", color = discord.Colour.green())
    return em

def ban_dm_x1(moderator: discord.User | discord.Member, reason: str, guildName: str) -> discord.Embed:
    em = discord.Embed(title=f"You have been banned!", description=f"`reason: ` {reason}", )
    em.set_footer(text=f"Banned from {guildName} by {moderator.name}")
    return em

def warn_x0(user: discord.Member | discord.User) -> discord.Embed:
    em = discord.Embed(description=f"{user.global_name} has been warned.", color = discord.Colour.green())
    return em

def warn_dm_x1(moderator: discord.User | discord.Member, reason: str, guildName: str) -> discord.Embed:
    em = discord.Embed(title="You have been warned!", description=f"`Reason: ` {reason}")
    em.set_footer(text=f"Sent from {guildName}")
    return em