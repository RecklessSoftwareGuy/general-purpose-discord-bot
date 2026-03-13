import discord, asyncio, datetime
from discord.ext import commands
from views import embeds

class moderationCommands(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()        


    @commands.command(name="mute", aliases=["timeout"])
    async def mute(self, ctx: commands.Context, user: discord.Member, duration: int = 6, *, reason: str = "None"):
        asyncio.gather(user.timeout(datetime.timedelta(hours=duration)), ctx.reply(embed=embeds.muted_x0(user, duration)), user.send(embed=embeds.muted_dm_x1(ctx.author, duration, reason)))

    @commands.command(name="remove_user", aliases=["kick"])
    async def remove_user(self, ctx: commands.Context, user: discord.Member, *, reason: str):
        if ctx.guild:
            await user.send(embed=embeds.kick_dm_x1(ctx.author, reason, ctx.guild.name))
            asyncio.gather(user.kick(reason=reason), ctx.reply(embed=embeds.kick_x0(user, reason)))
    
    @commands.command(name="ban_user", aliases=["ban"])
    async def ban_user(self, ctx: commands.Context, user: discord.Member, delete_after: int = 7, *, reason: str):
        if ctx.guild:
            await user.send(embed=embeds.ban_dm_x1(ctx.author, reason, ctx.guild.name))
            asyncio.gather(ctx.reply(embed=embeds.ban_x0(user)), user.ban(delete_message_days=delete_after))

    @commands.command(name="warn_user", aliases=["warn"])
    async def warn_user(self, ctx: commands.Context, user: discord.Member, *, reason: str):
        if ctx.guild and user in ctx.guild.members:
            await ctx.send(embed=embeds.warn_x0(user))
            await user.send(embed=embeds.warn_dm_x1(ctx.author, reason, ctx.guild.name))
            asyncio.gather(ctx.send(embed=embeds.warn_x0(user)), user.send(embed=embeds.warn_dm_x1(ctx.author, reason, ctx.guild.name)))

async def setup(bot: commands.Bot):
    await bot.add_cog(moderationCommands(bot))