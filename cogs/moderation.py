import discord, asyncio, datetime
from discord.ext import commands, tasks
from views import embeds
from functions import database_functions as db
from functions import moderation_functions as mf
from functions import utility_functions as uf


class moderationCommands(commands.Cog):
    """🔨 Moderation commands for managing server members."""
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.check_temp_bans.start()
        print(f"Initialized: {self.__cog_name__}")
        super().__init__()

    def cog_unload(self):
        self.check_temp_bans.cancel()

    # ── Temp Ban Loop ──────────────────────────────────────────────────────

    @tasks.loop(minutes=1)
    async def check_temp_bans(self):
        """Check for expired temp bans and unban users."""
        expired = await db.get_expired_temp_bans()
        for ban in expired:
            guild = self.bot.get_guild(ban["guild_id"])
            if guild:
                try:
                    user = await self.bot.fetch_user(ban["user_id"])
                    await guild.unban(user, reason="Temp ban expired")
                except Exception:
                    pass
            await db.remove_temp_ban(ban["guild_id"], ban["user_id"])

    @check_temp_bans.before_loop
    async def before_check_temp_bans(self):
        await self.bot.wait_until_ready()

    # ── Mute / Unmute ──────────────────────────────────────────────────────

    @commands.command(name="mute", aliases=["timeout"])
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def mute(self, ctx: commands.Context, user: discord.Member, duration: int = 6, *, reason: str = "No reason provided"):
        if ctx.guild:
            await user.timeout(datetime.timedelta(hours=duration))
            await ctx.reply(embed=embeds.muted_x0(user, duration))
            await mf.process_mute(ctx.guild.id, user.id, ctx.author.id, reason, f"{duration}h")
            try:
                await user.send(embed=embeds.muted_dm_x1(ctx.author, duration, reason))
            except discord.Forbidden:
                pass
            log_embed = mf.build_mod_log_embed("mute", ctx.author, user, reason, f"{duration}h")
            await mf.send_mod_log(ctx.guild, log_embed)
    
    @commands.command(name="unmute", aliases=["untimeout"])
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def unmute(self, ctx: commands.Context, user: discord.Member):
        if ctx.guild:
            await user.edit(timed_out_until=None)
            await ctx.reply(embed=embeds.unmuted_x0(user))
            await mf.process_unmute(ctx.guild.id, user.id, ctx.author.id)
            log_embed = mf.build_mod_log_embed("unmute", ctx.author, user)
            await mf.send_mod_log(ctx.guild, log_embed)

    # ── Kick ───────────────────────────────────────────────────────────────

    @commands.command(name="remove_user", aliases=["kick"])
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def remove_user(self, ctx: commands.Context, user: discord.Member, *, reason: str = "No reason provided"):
        if ctx.guild:
            try:
                await user.send(embed=embeds.kick_dm_x1(ctx.author, reason, ctx.guild.name))
            except discord.Forbidden:
                pass
            await user.kick(reason=reason)
            await ctx.reply(embed=embeds.kick_x0(user, reason))
            await mf.process_kick(ctx.guild.id, user.id, ctx.author.id, reason)
            log_embed = mf.build_mod_log_embed("kick", ctx.author, user, reason)
            await mf.send_mod_log(ctx.guild, log_embed)
    
    # ── Ban / Unban / Tempban / Softban ───────────────────────────────────

    @commands.command(name="ban_user", aliases=["ban"])
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban_user(self, ctx: commands.Context, user: discord.Member, delete_after: int = 0, *, reason: str = "No reason provided"):
        if ctx.guild and delete_after >= 0:
            try:
                await user.send(embed=embeds.ban_dm_x1(ctx.author, reason, ctx.guild.name))
            except discord.Forbidden:
                pass
            await user.ban(delete_message_days=delete_after, reason=reason)
            await ctx.reply(embed=embeds.ban_x0(user))
            await mf.process_ban(ctx.guild.id, user.id, ctx.author.id, reason)
            log_embed = mf.build_mod_log_embed("ban", ctx.author, user, reason)
            await mf.send_mod_log(ctx.guild, log_embed)

    @commands.command(name="unban_user", aliases=["unban"])
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban_user(self, ctx: commands.Context, user: discord.User):
        if ctx.guild:
            try:
                await ctx.guild.unban(user)
                await ctx.reply(embed=embeds.unban_x0(user))
                await mf.process_unban(ctx.guild.id, user.id, ctx.author.id)
                log_embed = mf.build_mod_log_embed("unban", ctx.author, user)
                await mf.send_mod_log(ctx.guild, log_embed)
            except discord.NotFound:
                await ctx.send(embed=embeds.error_x0(f"`{user.name}` is not banned."))

    @commands.command(name="tempban")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def tempban(self, ctx: commands.Context, user: discord.Member, duration: str = "1d", *, reason: str = "No reason provided"):
        """Temporarily ban a user. Duration: e.g., 1d, 12h, 1w"""
        if ctx.guild:
            td = uf.parse_duration(duration)
            if not td:
                await ctx.send(embed=embeds.error_x0("Invalid duration! Use formats like `1d`, `12h`, `1w`."))
                return
            duration_str = uf.format_duration(td)
            import time
            unban_at = int(time.time() + td.total_seconds())
            try:
                await user.send(embed=embeds.tempban_dm_x1(ctx.author, reason, ctx.guild.name, duration_str))
            except discord.Forbidden:
                pass
            await user.ban(reason=f"Temp ban: {duration_str} — {reason}")
            await db.add_temp_ban(ctx.guild.id, user.id, ctx.author.id, reason, unban_at)
            await ctx.reply(embed=embeds.tempban_x0(user, duration_str))
            await mf.process_ban(ctx.guild.id, user.id, ctx.author.id, reason, duration_str)
            log_embed = mf.build_mod_log_embed("tempban", ctx.author, user, reason, duration_str)
            await mf.send_mod_log(ctx.guild, log_embed)

    @commands.command(name="softban_user", aliases=["softban"])
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def softban_user(self, ctx: commands.Context, user: discord.Member | discord.User, delete_duration: int = 7):
        if ctx.guild:
            try:
                await user.send(embed=embeds.softban_dm_x1(user, ctx.guild.name))
            except discord.Forbidden:
                pass
            await ctx.guild.ban(user, delete_message_days=delete_duration, reason="Softban")
            await ctx.guild.unban(user, reason="Softban — unban after message purge")
            await ctx.reply(embed=embeds.softban_x0(user))
            await db.log_mod_action(ctx.guild.id, user.id, ctx.author.id, "softban")
            log_embed = mf.build_mod_log_embed("softban", ctx.author, user)
            await mf.send_mod_log(ctx.guild, log_embed)

    # ── Warnings ───────────────────────────────────────────────────────────

    @commands.command(name="warn_user", aliases=["warn"])
    @commands.has_permissions(moderate_members=True)
    async def warn_user(self, ctx: commands.Context, user: discord.Member, *, reason: str = "No reason provided"):
        if ctx.guild:
            warning_id, total = await mf.process_warning(ctx.guild.id, user.id, ctx.author.id, reason)
            await ctx.send(embed=embeds.warn_x0(user, warning_id, total))
            try:
                await user.send(embed=embeds.warn_dm_x1(ctx.author, reason, ctx.guild.name))
            except discord.Forbidden:
                pass
            log_embed = mf.build_mod_log_embed("warn", ctx.author, user, reason, extra=f"Warning #{warning_id} (Total: {total})")
            await mf.send_mod_log(ctx.guild, log_embed)

    @commands.command(name="warnings", aliases=["warns"])
    @commands.has_permissions(moderate_members=True)
    async def warnings(self, ctx: commands.Context, user: discord.Member | None = None):
        """View warnings for a user."""
        if not ctx.guild:
            return
        target = user or ctx.author
        warns = await db.get_warnings(ctx.guild.id, target.id)
        em = mf.format_warnings_list(warns, target)
        await ctx.send(embed=em)

    @commands.command(name="delwarn", aliases=["removewarn"])
    @commands.has_permissions(moderate_members=True)
    async def delwarn(self, ctx: commands.Context, warning_id: int):
        """Delete a specific warning by ID."""
        if ctx.guild:
            success = await db.delete_warning(warning_id, ctx.guild.id)
            if success:
                await ctx.send(embed=embeds.delwarn_x0(warning_id))
            else:
                await ctx.send(embed=embeds.error_x0(f"Warning #{warning_id} not found."))

    @commands.command(name="clearwarnings", aliases=["clearwarns"])
    @commands.has_permissions(moderate_members=True)
    async def clearwarnings(self, ctx: commands.Context, user: discord.Member):
        """Clear all warnings for a user."""
        if ctx.guild:
            count = await db.clear_warnings(ctx.guild.id, user.id)
            await ctx.send(embed=embeds.clearwarnings_x0(user, count))

    @commands.command(name="modhistory", aliases=["modlog"])
    @commands.has_permissions(moderate_members=True)
    async def modhistory(self, ctx: commands.Context, user: discord.Member):
        """View a user's moderation action history."""
        if ctx.guild:
            em = await mf.get_moderation_history_embed(ctx.guild.id, user)
            await ctx.send(embed=em)

    # ── Channel Management ────────────────────────────────────────────────

    @commands.command(name="mass_delete_message", aliases=["purge"])
    @commands.has_permissions(moderate_members=True, manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def mass_delete_message(self, ctx: commands.Context, limit: int = 1):
        if isinstance(ctx.channel, discord.TextChannel) and limit <= 1000:
            try:
                await ctx.message.delete()
                deleted = await ctx.channel.purge(limit=limit, check=lambda message: not message.pinned)
                msg = await ctx.send(embed=embeds.success_x0(f"Purged **{len(deleted)}** messages."))
                await asyncio.sleep(3)
                await msg.delete()
            except Exception:
                await ctx.send(embed=embeds.error_x0("Unable to purge channel."))

    @commands.command(name="lock_channel", aliases=["lock"])
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(send_messages=True, manage_channels=True)
    async def lock_channel(self, ctx: commands.Context, channel: discord.TextChannel | None = None):
        channel = channel or (ctx.channel if isinstance(ctx.channel, discord.TextChannel) else None)
        if ctx.guild and channel:
            await channel.set_permissions(ctx.guild.default_role, send_messages=False)
            await ctx.reply(embed=embeds.lockchannel_x0())
        else:
            await ctx.send(embed=embeds.error_x0("Unable to lock channel (wrong channel type)."))

    @commands.command(name="unlock_channel", aliases=["unlock"])
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(send_messages=True, manage_channels=True)
    async def unlock_channel(self, ctx: commands.Context, channel: discord.TextChannel | None = None):
        channel = channel or (ctx.channel if isinstance(ctx.channel, discord.TextChannel) else None)
        if ctx.guild and channel:
            await channel.set_permissions(ctx.guild.default_role, send_messages=True)
            await ctx.reply(embed=embeds.unlockchannel_x0())
        else:
            await ctx.send(embed=embeds.error_x0("Unable to unlock channel (wrong channel type)."))

    @commands.command(name="slowmode_channel", aliases=["slowmode"])
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def slowmode_channel(self, ctx: commands.Context, slowmode_delay: int = 5, channel: discord.TextChannel | None = None):
        channel = channel or (ctx.channel if isinstance(ctx.channel, discord.TextChannel) else None)
        if ctx.guild and channel:
            await channel.edit(slowmode_delay=slowmode_delay)
            await ctx.reply(embed=embeds.success_x0(f"Slowmode set to **{slowmode_delay}s** in {channel.mention}."))
        else:
            await ctx.send(embed=embeds.error_x0("Unable to set slowmode (wrong channel type)."))

    # ── Mod Config ─────────────────────────────────────────────────────────

    @commands.command(name="setmodlog")
    @commands.has_permissions(manage_guild=True)
    async def setmodlog(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the moderation log channel."""
        if ctx.guild:
            await db.update_guild_config(ctx.guild.id, mod_log_channel_id=channel.id)
            await ctx.send(embed=embeds.config_set_x0("Mod Log Channel", channel.mention))


async def setup(bot: commands.Bot):
    await bot.add_cog(moderationCommands(bot))