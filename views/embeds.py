import discord

def muted_x0(user: discord.Member | discord.User, duration: int) -> discord.Embed:
    em = discord.Embed(description=f"`{user.name}` was muted for {duration} hours.", color=discord.Colour.dark_orange())
    return em

def unmuted_x0(user: discord.Member | discord.User) -> discord.Embed:
    em = discord.Embed(description=f"`{user.name}` was unmuted", colour=discord.Colour.green())
    return em

def muted_dm_x1(moderator: discord.User | discord.Member, duration: int, reason: str) -> discord.Embed:
    em = discord.Embed(title="You have been muted", description=f"Muted by {moderator.mention} for {duration} hours.\n`Reason: {reason}`",  color=discord.Colour.green())
    return em

def kick_x0(user: discord.Member | discord.User, reason: str) -> discord.Embed:
    em = discord.Embed(description=f"Kicked {user.name}", color=discord.Colour.dark_orange())
    return em

def kick_dm_x1(moderator: discord.Member | discord.User, reason: str, guildName: str) -> discord.Embed:
    em = discord.Embed(title=f"You have been kicked from {guildName}", description=f"`Reason: {reason}`", color=discord.Colour.yellow())
    em.set_footer(text=f"Kicked by {moderator.name}")
    return em

def ban_x0(user: discord.Member | discord.User) -> discord.Embed:
    em = discord.Embed(description=f"Banned {user.name}", color = discord.Colour.dark_orange())
    return em

def unban_x0(user: discord.User) -> discord.Embed:
    em = discord.Embed(description=f"Unbanned {user.name}", color = discord.Colour.green())
    return em

def ban_dm_x1(moderator: discord.User | discord.Member, reason: str, guildName: str) -> discord.Embed:
    em = discord.Embed(title=f"You have been banned!", description=f"`reason: {reason}`", colour=discord.Colour.red())
    em.set_footer(text=f"Banned from {guildName} by {moderator.name}")
    return em

def warn_x0(user: discord.Member | discord.User) -> discord.Embed:
    em = discord.Embed(description=f"{user.global_name} has been warned.", color = discord.Colour.dark_orange())
    return em

def warn_dm_x1(moderator: discord.User | discord.Member, reason: str, guildName: str) -> discord.Embed:
    em = discord.Embed(title="You have been warned!", description=f"`Reason: {reason}`", color=discord.Colour.light_grey())
    em.set_footer(text=f"Sent from {guildName}")
    return em

def mprofile_x0(userData: dict) -> discord.Embed:
    em = discord.Embed(title=f"{userData["username"]}'s Server Profile", color=discord.Colour.og_blurple())
    em.add_field(name="Created:", value=f"<t:{userData["createdAt"]}:R>", inline=True)
    em.add_field(name="Joined:", value=f"<t:{userData["joinedAt"]}:R>", inline=True)
    em.add_field(name="Messages:", value=f"{userData["nMessages"]} messages", inline=False)
    # em.add_field(name="Last Online:", value=f"{userData["lastOnline"]}", inline=True)
    try:
        em.set_author(name=f"{userData["authorName"]}", icon_url=f"{userData["authorAvatar"].url}")
    except:
        pass
    em.set_footer(text=f"{userData["servername"]}", icon_url={userData["serverAvatar"]})
    return em

def softban_x0(user: discord.Member | discord.User) -> discord.Embed:
    em = discord.Embed(description=f"{user.global_name} has been softbanned!", color=discord.Colour.red())
    return em

def softban_dm_x1(user: discord.Member | discord.User, guildName: str) -> discord.Embed:
    em = discord.Embed(title=f"You have been softbanned from {guildName}! Please use a new invite if you wish to re-join")
    return em

def lockchannel_x0() -> discord.Embed:
    em = discord.Embed(title="Channel Locked", color = discord.Colour.yellow())
    return em

def unlockchannel_x0() -> discord.Embed:
    em = discord.Embed(title="Channel unlocked", color = discord.Colour.yellow())
    return em