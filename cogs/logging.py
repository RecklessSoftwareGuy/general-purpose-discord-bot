import discord
from discord.ext import commands
from functions import database_functions as db
from views import embeds


class loggingCommands(commands.Cog):
    """📝 Server event logging."""
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        print(f"Initialized: {self.__cog_name__}")
        super().__init__()

    async def _get_log_channel(self, guild: discord.Guild) -> discord.TextChannel | None:
        config = await db.get_guild_config(guild.id)
        if config and config.get("log_channel_id"):
            channel = guild.get_channel(config["log_channel_id"])
            if isinstance(channel, discord.TextChannel):
                return channel
        return None

    async def _send_log(self, guild: discord.Guild, embed: discord.Embed):
        channel = await self._get_log_channel(guild)
        if channel:
            try:
                await channel.send(embed=embed)
            except discord.Forbidden:
                pass

    # ── Message Events ────────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        await self._send_log(message.guild, embeds.message_delete_log(message))

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot or not before.guild:
            return
        if before.content == after.content:
            return
        await self._send_log(before.guild, embeds.message_edit_log(before, after))

    # ── Member Events ─────────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await self._send_log(member.guild, embeds.member_join_log(member))

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        await self._send_log(member.guild, embeds.member_leave_log(member))

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.roles != after.roles:
            await self._send_log(after.guild, embeds.role_update_log(before, after))

    # ── Voice Events ──────────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if before.channel == after.channel:
            return  # Only log join/leave/move
        await self._send_log(member.guild, embeds.voice_log(member, before, after))

    # ── Channel Events ────────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        em = discord.Embed(
            title="📁 Channel Created",
            description=f"**Name:** {channel.mention}\n**Type:** {str(channel.type).replace('_', ' ').title()}",
            colour=discord.Colour.green(),
            timestamp=discord.utils.utcnow()
        )
        em.set_footer(text=f"Channel ID: {channel.id}")
        await self._send_log(channel.guild, em)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        em = discord.Embed(
            title="📁 Channel Deleted",
            description=f"**Name:** #{channel.name}\n**Type:** {str(channel.type).replace('_', ' ').title()}",
            colour=discord.Colour.red(),
            timestamp=discord.utils.utcnow()
        )
        em.set_footer(text=f"Channel ID: {channel.id}")
        await self._send_log(channel.guild, em)

    # ── Config ────────────────────────────────────────────────────────────

    @commands.command(name="setlogchannel")
    @commands.has_permissions(manage_guild=True)
    async def setlogchannel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the event logging channel."""
        if ctx.guild:
            await db.update_guild_config(ctx.guild.id, log_channel_id=channel.id)
            await ctx.send(embed=embeds.config_set_x0("Log Channel", channel.mention))

    @commands.command(name="removelogchannel")
    @commands.has_permissions(manage_guild=True)
    async def removelogchannel(self, ctx: commands.Context):
        """Remove the event logging channel."""
        if ctx.guild:
            await db.update_guild_config(ctx.guild.id, log_channel_id=None)
            await ctx.send(embed=embeds.success_x0("Log channel has been removed."))


async def setup(bot: commands.Bot):
    await bot.add_cog(loggingCommands(bot))
