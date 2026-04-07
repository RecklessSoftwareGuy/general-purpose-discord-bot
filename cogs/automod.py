import discord
from discord.ext import commands
from functions import database_functions as db
from functions import automod_functions as af
from functions import moderation_functions as mf
from views import embeds


class automodCommands(commands.Cog):
    """🛡️ Auto-Moderation to protect your server."""
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        print(f"Initialized: {self.__cog_name__}")
        super().__init__()

    @commands.Cog.listener(name="on_message")
    async def automod_listener(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        if isinstance(message.author, discord.Member) and message.author.guild_permissions.manage_messages:
            return  # Skip mods

        config = await af.get_automod_config(message.guild.id)
        if not config["enabled"]:
            return

        violated = False
        reason = ""

        # Anti-spam
        if config["anti_spam"] and af.check_spam(message.author.id, message.guild.id):
            violated = True
            reason = "Spam detection — sending messages too quickly"
            af.clear_spam_cache(message.author.id)

        # Anti-invite
        if not violated and config["anti_invite"] and af.check_invite_link(message.content):
            violated = True
            reason = "Discord invite link detected"

        # Anti-mass-mention
        if not violated and config["anti_massmention"]:
            if af.check_mass_mention(message.content, len(message.mentions), config["massmention_threshold"]):
                violated = True
                reason = f"Mass mention ({len(message.mentions)} mentions)"

        # Bad word filter
        if not violated:
            badwords = await db.get_badwords(message.guild.id)
            if badwords and af.check_badwords(message.content, badwords):
                violated = True
                reason = "Blocked word detected"

        if violated:
            try:
                await message.delete()
            except discord.Forbidden:
                pass

            try:
                await message.channel.send(
                    f"{message.author.mention}, your message was removed. **Reason:** {reason}",
                    delete_after=5
                )
            except discord.Forbidden:
                pass

            # Log to mod channel
            if isinstance(message.author, discord.Member):
                log_em = embeds.automod_action_x0(message.author, "Message Deleted", reason)
                await mf.send_mod_log(message.guild, log_em)

    # ── Automod Config Commands ───────────────────────────────────────────

    @commands.group(name="automod", invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def automod(self, ctx: commands.Context):
        """View or configure auto-moderation settings."""
        if not ctx.guild:
            return
        config = await af.get_automod_config(ctx.guild.id)
        em = discord.Embed(title="🛡️ AutoMod Settings", colour=discord.Colour.blurple())
        em.add_field(name="Enabled", value="✅" if config["enabled"] else "❌", inline=True)
        em.add_field(name="Anti-Spam", value="✅" if config["anti_spam"] else "❌", inline=True)
        em.add_field(name="Anti-Invite", value="✅" if config["anti_invite"] else "❌", inline=True)
        em.add_field(name="Anti-Mass Mention", value="✅" if config["anti_massmention"] else "❌", inline=True)
        em.add_field(name="Mass Mention Threshold", value=str(config["massmention_threshold"]), inline=True)
        badwords = await db.get_badwords(ctx.guild.id)
        em.add_field(name="Blocked Words", value=str(len(badwords)), inline=True)
        await ctx.send(embed=em)

    @automod.command(name="enable")
    @commands.has_permissions(manage_guild=True)
    async def automod_enable(self, ctx: commands.Context):
        """Enable auto-moderation."""
        if ctx.guild:
            await db.update_guild_config(ctx.guild.id, automod_enabled=1)
            await ctx.send(embed=embeds.success_x0("AutoMod **enabled**."))

    @automod.command(name="disable")
    @commands.has_permissions(manage_guild=True)
    async def automod_disable(self, ctx: commands.Context):
        """Disable auto-moderation."""
        if ctx.guild:
            await db.update_guild_config(ctx.guild.id, automod_enabled=0)
            await ctx.send(embed=embeds.success_x0("AutoMod **disabled**."))

    @automod.command(name="antispam")
    @commands.has_permissions(manage_guild=True)
    async def automod_antispam(self, ctx: commands.Context, toggle: bool):
        """Toggle anti-spam. Usage: automod antispam true/false"""
        if ctx.guild:
            await db.update_guild_config(ctx.guild.id, automod_anti_spam=int(toggle))
            state = "enabled" if toggle else "disabled"
            await ctx.send(embed=embeds.success_x0(f"Anti-spam **{state}**."))

    @automod.command(name="antiinvite")
    @commands.has_permissions(manage_guild=True)
    async def automod_antiinvite(self, ctx: commands.Context, toggle: bool):
        """Toggle anti-invite. Usage: automod antiinvite true/false"""
        if ctx.guild:
            await db.update_guild_config(ctx.guild.id, automod_anti_invite=int(toggle))
            state = "enabled" if toggle else "disabled"
            await ctx.send(embed=embeds.success_x0(f"Anti-invite **{state}**."))

    @automod.command(name="antimention")
    @commands.has_permissions(manage_guild=True)
    async def automod_antimention(self, ctx: commands.Context, toggle: bool, threshold: int = 5):
        """Toggle anti-mass-mention. Usage: automod antimention true/false [threshold]"""
        if ctx.guild:
            await db.update_guild_config(
                ctx.guild.id,
                automod_anti_massmention=int(toggle),
                automod_massmention_threshold=threshold
            )
            state = "enabled" if toggle else "disabled"
            await ctx.send(embed=embeds.success_x0(f"Anti-mass-mention **{state}** (threshold: {threshold})."))

    @automod.command(name="addword")
    @commands.has_permissions(manage_guild=True)
    async def automod_addword(self, ctx: commands.Context, *, word: str):
        """Add a word to the blocked words list."""
        if ctx.guild:
            added = await db.add_badword(ctx.guild.id, word)
            if added:
                await ctx.send(embed=embeds.success_x0(f"Added `{word}` to blocked words."))
            else:
                await ctx.send(embed=embeds.error_x0(f"`{word}` is already blocked."))

    @automod.command(name="removeword")
    @commands.has_permissions(manage_guild=True)
    async def automod_removeword(self, ctx: commands.Context, *, word: str):
        """Remove a word from the blocked words list."""
        if ctx.guild:
            removed = await db.remove_badword(ctx.guild.id, word)
            if removed:
                await ctx.send(embed=embeds.success_x0(f"Removed `{word}` from blocked words."))
            else:
                await ctx.send(embed=embeds.error_x0(f"`{word}` is not in the blocked list."))

    @automod.command(name="wordlist")
    @commands.has_permissions(manage_guild=True)
    async def automod_wordlist(self, ctx: commands.Context):
        """View the blocked words list."""
        if ctx.guild:
            words = await db.get_badwords(ctx.guild.id)
            if words:
                word_list = ", ".join(f"`{w}`" for w in words)
                em = discord.Embed(title="🚫 Blocked Words", description=word_list, colour=discord.Colour.red())
            else:
                em = discord.Embed(title="🚫 Blocked Words", description="No blocked words set.", colour=discord.Colour.green())
            await ctx.send(embed=em)


async def setup(bot: commands.Bot):
    await bot.add_cog(automodCommands(bot))
