import discord
from discord.ext import commands
from functions import database_functions as db
from views import embeds


class welcomeCommands(commands.Cog):
    """👋 Welcome and leave messages, autorole on join."""
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        print(f"Initialized: {self.__cog_name__}")
        super().__init__()

    @commands.Cog.listener(name="on_member_join")
    async def on_member_join(self, member: discord.Member):
        config = await db.get_guild_config(member.guild.id)
        if not config:
            return

        # Welcome message
        if config.get("welcome_channel_id"):
            channel = member.guild.get_channel(config["welcome_channel_id"])
            if channel and isinstance(channel, discord.TextChannel):
                message = config.get("welcome_message", "Welcome to the server, {user}!")
                try:
                    await channel.send(embed=embeds.welcome_x0(member, message))
                except discord.Forbidden:
                    pass

        # Autorole
        if config.get("autorole_id"):
            role = member.guild.get_role(config["autorole_id"])
            if role:
                try:
                    await member.add_roles(role, reason="Autorole on join")
                except discord.Forbidden:
                    pass

    @commands.Cog.listener(name="on_member_remove")
    async def on_member_remove(self, member: discord.Member):
        config = await db.get_guild_config(member.guild.id)
        if not config:
            return

        if config.get("leave_channel_id"):
            channel = member.guild.get_channel(config["leave_channel_id"])
            if channel and isinstance(channel, discord.TextChannel):
                message = config.get("leave_message", "Goodbye, {user}!")
                try:
                    await channel.send(embed=embeds.leave_x0(member, message))
                except discord.Forbidden:
                    pass

    # ── Config Commands ───────────────────────────────────────────────────

    @commands.command(name="setwelcome")
    @commands.has_permissions(manage_guild=True)
    async def setwelcome(self, ctx: commands.Context, channel: discord.TextChannel, *, message: str = "Welcome to the server, {user}!"):
        """Set the welcome channel and message. Placeholders: {user}, {server}, {count}"""
        if ctx.guild:
            await db.update_guild_config(ctx.guild.id, welcome_channel_id=channel.id, welcome_message=message)
            await ctx.send(embed=embeds.config_set_x0("Welcome Channel", f"{channel.mention}\n**Message:** {message}"))

    @commands.command(name="setleave")
    @commands.has_permissions(manage_guild=True)
    async def setleave(self, ctx: commands.Context, channel: discord.TextChannel, *, message: str = "Goodbye, {user}!"):
        """Set the leave channel and message. Placeholders: {user}, {server}"""
        if ctx.guild:
            await db.update_guild_config(ctx.guild.id, leave_channel_id=channel.id, leave_message=message)
            await ctx.send(embed=embeds.config_set_x0("Leave Channel", f"{channel.mention}\n**Message:** {message}"))

    @commands.command(name="setautorole")
    @commands.has_permissions(manage_guild=True)
    async def setautorole(self, ctx: commands.Context, role: discord.Role):
        """Set a role to be automatically assigned when a member joins."""
        if ctx.guild:
            await db.update_guild_config(ctx.guild.id, autorole_id=role.id)
            await ctx.send(embed=embeds.config_set_x0("Autorole", role.mention))

    @commands.command(name="removeautorole")
    @commands.has_permissions(manage_guild=True)
    async def removeautorole(self, ctx: commands.Context):
        """Remove the autorole setting."""
        if ctx.guild:
            await db.update_guild_config(ctx.guild.id, autorole_id=None)
            await ctx.send(embed=embeds.success_x0("Autorole has been removed."))

    @commands.command(name="testwelcome")
    @commands.has_permissions(manage_guild=True)
    async def testwelcome(self, ctx: commands.Context):
        """Test the welcome message with yourself."""
        if ctx.guild and isinstance(ctx.author, discord.Member):
            config = await db.get_guild_config(ctx.guild.id)
            if config and config.get("welcome_channel_id"):
                message = config.get("welcome_message", "Welcome to the server, {user}!")
                await ctx.send(embed=embeds.welcome_x0(ctx.author, message))
            else:
                await ctx.send(embed=embeds.error_x0("No welcome channel is set. Use `setwelcome` first."))


async def setup(bot: commands.Bot):
    await bot.add_cog(welcomeCommands(bot))
