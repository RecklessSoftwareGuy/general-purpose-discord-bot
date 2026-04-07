import discord
from discord.ext import commands
from functions import database_functions as db
from views import embeds


class starboardCommands(commands.Cog):
    """⭐ Starboard — highlight popular messages."""
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        print(f"Initialized: {self.__cog_name__}")
        super().__init__()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if not payload.guild_id:
            return
        await self._handle_star(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if not payload.guild_id:
            return
        await self._handle_star(payload)

    async def _handle_star(self, payload: discord.RawReactionActionEvent):
        guild = self.bot.get_guild(payload.guild_id)  # type: ignore
        if not guild:
            return

        config = await db.get_guild_config(guild.id)
        if not config or not config.get("starboard_channel_id"):
            return

        star_emoji = config.get("starboard_emoji", "⭐")
        threshold = config.get("starboard_threshold", 3)

        if str(payload.emoji) != star_emoji:
            return

        starboard_channel = guild.get_channel(config["starboard_channel_id"])
        if not starboard_channel or not isinstance(starboard_channel, discord.TextChannel):
            return

        # Don't starboard messages from the starboard channel
        if payload.channel_id == starboard_channel.id:
            return

        source_channel = guild.get_channel(payload.channel_id)
        if not source_channel or not isinstance(source_channel, discord.TextChannel):
            return

        try:
            message = await source_channel.fetch_message(payload.message_id)
        except (discord.NotFound, discord.HTTPException):
            return

        # Count star reactions
        star_count = 0
        for reaction in message.reactions:
            if str(reaction.emoji) == star_emoji:
                star_count = reaction.count
                break

        entry = await db.get_starboard_entry(guild.id, message.id)

        if star_count < threshold:
            # Remove from starboard if below threshold
            if entry:
                try:
                    sb_msg = await starboard_channel.fetch_message(entry["starboard_message_id"])
                    await sb_msg.delete()
                except (discord.NotFound, discord.HTTPException):
                    pass
                await db.delete_starboard_entry(guild.id, message.id)
            return

        em = embeds.starboard_x0(message, star_count, star_emoji)

        if entry:
            # Update existing starboard message
            try:
                sb_msg = await starboard_channel.fetch_message(entry["starboard_message_id"])
                await sb_msg.edit(content=f"{star_emoji} **{star_count}** | {source_channel.mention}", embed=em)
                await db.upsert_starboard_entry(guild.id, message.id, sb_msg.id, source_channel.id, message.author.id, star_count)
            except (discord.NotFound, discord.HTTPException):
                pass
        else:
            # Create new starboard message
            try:
                sb_msg = await starboard_channel.send(
                    content=f"{star_emoji} **{star_count}** | {source_channel.mention}",
                    embed=em
                )
                await db.upsert_starboard_entry(guild.id, message.id, sb_msg.id, source_channel.id, message.author.id, star_count)
            except discord.HTTPException:
                pass

    # ── Config Commands ───────────────────────────────────────────────────

    @commands.group(name="starboard", invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def starboard(self, ctx: commands.Context):
        """Starboard configuration."""
        if not ctx.guild:
            return
        config = await db.get_guild_config(ctx.guild.id)
        em = discord.Embed(title="⭐ Starboard Settings", colour=discord.Colour.gold())
        if config and config.get("starboard_channel_id"):
            channel = ctx.guild.get_channel(config["starboard_channel_id"])
            em.add_field(name="Channel", value=channel.mention if channel else "Not set", inline=True)
            em.add_field(name="Threshold", value=str(config.get("starboard_threshold", 3)), inline=True)
            em.add_field(name="Emoji", value=config.get("starboard_emoji", "⭐"), inline=True)
        else:
            em.description = "Starboard is not set up. Use `starboard setup <channel> [threshold]`."
        await ctx.send(embed=em)

    @starboard.command(name="setup")
    @commands.has_permissions(manage_guild=True)
    async def starboard_setup(self, ctx: commands.Context, channel: discord.TextChannel, threshold: int = 3):
        """Set up the starboard."""
        if ctx.guild:
            await db.update_guild_config(ctx.guild.id, starboard_channel_id=channel.id, starboard_threshold=threshold)
            await ctx.send(embed=embeds.success_x0(f"Starboard set to {channel.mention} with threshold **{threshold}**."))

    @starboard.command(name="threshold")
    @commands.has_permissions(manage_guild=True)
    async def starboard_threshold(self, ctx: commands.Context, threshold: int):
        """Change the star threshold."""
        if ctx.guild:
            await db.update_guild_config(ctx.guild.id, starboard_threshold=threshold)
            await ctx.send(embed=embeds.config_set_x0("Star Threshold", str(threshold)))

    @starboard.command(name="emoji")
    @commands.has_permissions(manage_guild=True)
    async def starboard_emoji(self, ctx: commands.Context, emoji: str):
        """Change the starboard emoji."""
        if ctx.guild:
            await db.update_guild_config(ctx.guild.id, starboard_emoji=emoji)
            await ctx.send(embed=embeds.config_set_x0("Starboard Emoji", emoji))


async def setup(bot: commands.Bot):
    await bot.add_cog(starboardCommands(bot))
