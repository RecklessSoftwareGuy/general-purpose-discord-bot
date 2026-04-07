import discord
from discord.ext import commands
from functions import database_functions as db
from views import embeds


class customCommands(commands.Cog):
    """📋 Per-guild custom text commands."""
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        print(f"Initialized: {self.__cog_name__}")
        super().__init__()

    @commands.Cog.listener(name="on_message")
    async def custom_command_listener(self, message: discord.Message):
        """Check if a message matches a custom command."""
        if message.author.bot or not message.guild:
            return

        # Get the prefix used
        prefixes = await self.bot.get_prefix(message)
        if isinstance(prefixes, str):
            prefixes = [prefixes]

        content = message.content
        used_prefix = None
        for prefix in prefixes:
            if content.startswith(prefix):
                used_prefix = prefix
                break

        if not used_prefix:
            return

        # Extract command name
        cmd_text = content[len(used_prefix):].strip().split()[0].lower() if content[len(used_prefix):].strip() else ""
        if not cmd_text:
            return

        # Don't override built-in commands
        if self.bot.get_command(cmd_text):
            return

        # Check for custom command
        response = await db.get_custom_command(message.guild.id, cmd_text)
        if response:
            await message.channel.send(response)

    # ── Management Commands ───────────────────────────────────────────────

    @commands.group(name="customcmd", aliases=["cc"], invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def customcmd(self, ctx: commands.Context):
        """Custom command management."""
        em = discord.Embed(
            title="📋 Custom Commands",
            description=(
                "`customcmd add <name> <response>` — Create a custom command\n"
                "`customcmd remove <name>` — Delete a custom command\n"
                "`customcmd list` — View all custom commands\n"
            ),
            colour=discord.Colour.blurple()
        )
        await ctx.send(embed=em)

    @customcmd.command(name="add", aliases=["create"])
    @commands.has_permissions(manage_guild=True)
    async def customcmd_add(self, ctx: commands.Context, name: str, *, response: str):
        """Create a custom command."""
        if not ctx.guild:
            return

        # Don't allow overriding built-in commands
        if self.bot.get_command(name):
            await ctx.send(embed=embeds.error_x0(f"`{name}` conflicts with a built-in command!"))
            return

        added = await db.add_custom_command(ctx.guild.id, name, response, ctx.author.id)
        if added:
            await ctx.send(embed=embeds.customcmd_added_x0(name))
        else:
            await ctx.send(embed=embeds.error_x0(f"Custom command `{name}` already exists!"))

    @customcmd.command(name="remove", aliases=["delete"])
    @commands.has_permissions(manage_guild=True)
    async def customcmd_remove(self, ctx: commands.Context, name: str):
        """Delete a custom command."""
        if ctx.guild:
            removed = await db.remove_custom_command(ctx.guild.id, name)
            if removed:
                await ctx.send(embed=embeds.customcmd_removed_x0(name))
            else:
                await ctx.send(embed=embeds.error_x0(f"Custom command `{name}` not found."))

    @customcmd.command(name="list")
    async def customcmd_list(self, ctx: commands.Context):
        """View all custom commands."""
        if ctx.guild:
            cmds = await db.get_all_custom_commands(ctx.guild.id)
            await ctx.send(embed=embeds.customcmd_list_x0(ctx.guild.name, cmds))


async def setup(bot: commands.Bot):
    await bot.add_cog(customCommands(bot))
