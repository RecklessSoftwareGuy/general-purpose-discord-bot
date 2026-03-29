import discord, asyncio, datetime
from discord.ext import commands
from views import embeds

class moderationCommands(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        print(f"Initialized: {self.__cog_name__}")
        super().__init__()        

    @commands.command(name="mute", aliases=["timeout"])
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def mute(self, ctx: commands.Context, user: discord.Member, duration: int = 6, *, reason: str = "None"):
        asyncio.gather(user.timeout(datetime.timedelta(hours=duration)), ctx.reply(embed=embeds.muted_x0(user, duration)), user.send(embed=embeds.muted_dm_x1(ctx.author, duration, reason)))
    
    @commands.command(name="unmute", aliases=["untimeout"])
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def unmute(self, ctx: commands.Context, user: discord.Member):
        asyncio.gather(user.edit(timed_out_until=None), ctx.reply(embed=embeds.unmuted_x0(user)))

    @commands.command(name="remove_user", aliases=["kick"])
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def remove_user(self, ctx: commands.Context, user: discord.Member, *, reason: str):
        if ctx.guild:
            await user.send(embed=embeds.kick_dm_x1(ctx.author, reason, ctx.guild.name))
            asyncio.gather(user.kick(reason=reason), ctx.reply(embed=embeds.kick_x0(user, reason)))
    
    @commands.command(name="ban_user", aliases=["ban"])
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban_user(self, ctx: commands.Context, user: discord.Member, delete_after: int = 0, *, reason: str = ""):
        if ctx.guild and delete_after >= 0:
            await user.send(embed=embeds.ban_dm_x1(ctx.author, reason, ctx.guild.name))
            asyncio.gather(ctx.reply(embed=embeds.ban_x0(user)), user.ban(delete_message_days=delete_after))
        else:
            await ctx.reply("Unable to ban: Follow the format: `ban <user> <delete_user_message_days> <reason>`")

    @commands.command(name="unban_user", aliases=["unban"])
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban_user(self, ctx: commands.Context, user: discord.User):
        if ctx.guild:
            try:
            #     banned_users = await ctx.guild.bans()
            #     for bm in banned_users:
            #         banned_user = bm.user
            #         if banned_user == user: break
                asyncio.gather(ctx.guild.unban(user), ctx.reply(embed=embeds.unban_x0(user)))
            except:
                await ctx.send(f"Unable to unban `{user.name}`")

    @commands.command(name="warn_user", aliases=["warn"])
    @commands.has_permissions(moderate_members=True)
    async def warn_user(self, ctx: commands.Context, user: discord.Member, *, reason: str):
        if ctx.guild and user in ctx.guild.members:
            asyncio.gather(ctx.send(embed=embeds.warn_x0(user)), user.send(embed=embeds.warn_dm_x1(ctx.author, reason, ctx.guild.name)))

    @commands.command(name="mass_delete_message", aliases=["purge"])
    @commands.has_permissions(moderate_members=True, manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def mass_delete_message(self, ctx: commands.Context, limit: int = 1):
        if limit <= 1000: #works for only text channel
            try:
                await ctx.message.delete()
                await ctx.channel.purge(limit=limit, check= lambda message: not message.pinned) #type: ignore
                await ctx.send(f"Purged `{limit}` messages successfully")
            except:
                await ctx.send(f"Unable to purge channel")

    @commands.command(name="softban_user", aliases=["softban"])
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def softban_user(self, ctx: commands.Context, user: discord.Member | discord.User, delete_duration: int = 7):
        if ctx.guild:
            await user.send(embed=embeds.softban_dm_x1(user, ctx.guild.name))
            await user.ban(delete_message_days=delete_duration) #type: ignore
            asyncio.gather(user.unban(), ctx.reply(embed=embeds.softban_x0(user))) #type: ignore

    @commands.command(name="lock_channel", aliases=["lock"])
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(send_messages=True, manage_channels=True)
    async def lock_channel(self, ctx: commands.Context, channel: discord.TextChannel | None = None):
        if not channel and channel is discord.TextChannel: channel = ctx.channel
        if ctx.guild and channel:
            asyncio.gather(ctx.reply(embed=embeds.lockchannel_x0()), channel.set_permissions(ctx.guild.default_role, send_messages=False))
        else:
            await ctx.send("Unable to lock channel (Wrong Channel Type)")


    @commands.command(name="unlock_channel", aliases=["unlock"])
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(send_messages=True, manage_channels=True)
    async def unlock_channel(self, ctx: commands.Context, channel: discord.TextChannel | None = None):
        if not channel and channel is discord.TextChannel: channel = ctx.channel
        if ctx.guild and channel:
            asyncio.gather(ctx.reply(embed=embeds.unlockchannel_x0()), channel.set_permissions(ctx.guild.default_role, send_messages=True))
        else:
            await ctx.send("Unable to unlock channel (Wrong Channel Type)")

    @commands.command(name="slowmode_channel", aliases=["slowmode"])
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_channels=True, bypass_slowmode=True, manage_messages=True)
    async def slowmode_channel(self, ctx: commands.Context, channel: discord.TextChannel | None = None, slowmode_delay: int = 5):
        if not channel and channel is discord.TextChannel: channel = ctx.channel
        if ctx.guild and channel:
            asyncio.gather(ctx.reply(), channel.edit(slowmode_delay=slowmode_delay))
        else:
            await ctx.send("Unable to set slowmode (Wrong channel type)")


async def setup(bot: commands.Bot):
    await bot.add_cog(moderationCommands(bot))