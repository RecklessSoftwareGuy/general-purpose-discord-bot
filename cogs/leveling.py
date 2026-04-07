import discord
from discord.ext import commands
from functions import database_functions as db
from functions import leveling_functions as lf
from views import embeds


class levelingCommands(commands.Cog):
    """📊 XP and leveling system."""
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        print(f"Initialized: {self.__cog_name__}")
        super().__init__()

    @commands.Cog.listener(name="on_message")
    async def xp_listener(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        # Check if leveling is enabled
        config = await db.get_guild_config(message.guild.id)
        if not config or not config.get("level_enabled"):
            return

        leveled_up, new_level = await lf.process_message_xp(message.guild.id, message.author.id)

        if leveled_up and isinstance(message.author, discord.Member):
            # Send level up notification
            level_channel_id = config.get("level_channel_id")
            target_channel = None
            if level_channel_id:
                target_channel = message.guild.get_channel(level_channel_id)
            if not target_channel:
                target_channel = message.channel

            if isinstance(target_channel, discord.TextChannel):
                await target_channel.send(embed=embeds.levelup_x0(message.author, new_level))

            # Check for level role rewards
            level_roles = await db.get_level_roles(message.guild.id)
            for lr in level_roles:
                if lr["level"] <= new_level:
                    role = message.guild.get_role(lr["role_id"])
                    if role and role not in message.author.roles:
                        try:
                            await message.author.add_roles(role, reason=f"Level {lr['level']} reward")
                        except discord.Forbidden:
                            pass

    @commands.command(name="rank", aliases=["level", "xp"])
    async def rank(self, ctx: commands.Context, user: discord.Member | None = None):
        """View your or another user's rank card."""
        if not ctx.guild:
            return
        target = user or (ctx.author if isinstance(ctx.author, discord.Member) else None)
        if not target or not isinstance(target, discord.Member):
            return

        data = await db.get_user_level(ctx.guild.id, target.id)
        current_xp, needed_xp = lf.xp_progress(data["xp"], data["level"])
        rank_pos = await lf.get_rank(ctx.guild.id, target.id)
        bar = lf.progress_bar(current_xp, needed_xp, 12)

        await ctx.send(embed=embeds.rank_x0(
            target, data["level"], data["xp"],
            current_xp, needed_xp, rank_pos, bar
        ))

    @commands.command(name="leaderboard", aliases=["lb", "top"])
    async def leaderboard(self, ctx: commands.Context):
        """View the server's XP leaderboard."""
        if not ctx.guild:
            return
        entries = await db.get_leaderboard(ctx.guild.id, 10)
        await ctx.send(embed=embeds.leaderboard_x0(ctx.guild, entries, self.bot))

    @commands.command(name="enableleveling")
    @commands.has_permissions(manage_guild=True)
    async def enableleveling(self, ctx: commands.Context):
        """Enable the leveling system."""
        if ctx.guild:
            await db.update_guild_config(ctx.guild.id, level_enabled=1)
            await ctx.send(embed=embeds.success_x0("Leveling system **enabled**."))

    @commands.command(name="disableleveling")
    @commands.has_permissions(manage_guild=True)
    async def disableleveling(self, ctx: commands.Context):
        """Disable the leveling system."""
        if ctx.guild:
            await db.update_guild_config(ctx.guild.id, level_enabled=0)
            await ctx.send(embed=embeds.success_x0("Leveling system **disabled**."))

    @commands.command(name="setlevelchannel")
    @commands.has_permissions(manage_guild=True)
    async def setlevelchannel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the channel for level-up notifications."""
        if ctx.guild:
            await db.update_guild_config(ctx.guild.id, level_channel_id=channel.id)
            await ctx.send(embed=embeds.config_set_x0("Level Channel", channel.mention))

    @commands.command(name="setlevelrole")
    @commands.has_permissions(manage_guild=True)
    async def setlevelrole(self, ctx: commands.Context, level: int, role: discord.Role):
        """Set a role reward for reaching a level."""
        if ctx.guild:
            await db.set_level_role(ctx.guild.id, level, role.id)
            await ctx.send(embed=embeds.success_x0(f"{role.mention} will be awarded at **Level {level}**."))

    @commands.command(name="removelevelrole")
    @commands.has_permissions(manage_guild=True)
    async def removelevelrole(self, ctx: commands.Context, level: int):
        """Remove a level role reward."""
        if ctx.guild:
            await db.remove_level_role(ctx.guild.id, level)
            await ctx.send(embed=embeds.success_x0(f"Removed role reward for **Level {level}**."))

    @commands.command(name="levelroles")
    async def levelroles(self, ctx: commands.Context):
        """View all level role rewards."""
        if not ctx.guild:
            return
        roles = await db.get_level_roles(ctx.guild.id)
        if not roles:
            await ctx.send(embed=embeds.info_x0("No level role rewards set."))
            return
        em = discord.Embed(title="🏆 Level Role Rewards", colour=discord.Colour.gold())
        for lr in roles:
            role = ctx.guild.get_role(lr["role_id"])
            role_text = role.mention if role else f"Unknown ({lr['role_id']})"
            em.add_field(name=f"Level {lr['level']}", value=role_text, inline=True)
        await ctx.send(embed=em)


async def setup(bot: commands.Bot):
    await bot.add_cog(levelingCommands(bot))
