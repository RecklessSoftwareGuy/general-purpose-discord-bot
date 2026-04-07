import discord, json
from discord.ext import commands
from views.views import HelpView


with open('assets/config.json', 'rb') as f:
    config = json.load(f)


class helpCommand(commands.Cog):
    """❓ Paginated help command."""
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        print(f"Initialized: {self.__cog_name__}")
        super().__init__()

    def _build_pages(self, ctx: commands.Context) -> list[discord.Embed]:
        prefix = config["prefix"][0]
        pages = []

        # Home page
        home = discord.Embed(
            title=f"📖 {self.bot.user.display_name} — Help",  # type: ignore
            description=(
                f"Use `{prefix}help <command>` for detailed info on a command.\n"
                f"Use the buttons below to navigate through categories.\n\n"
                f"**Prefix:** `{prefix}` or mention me"
            ),
            colour=discord.Colour.blurple()
        )
        if self.bot.user:
            home.set_thumbnail(url=self.bot.user.display_avatar.url)

        # List all cogs with their descriptions
        cog_list = []
        for cog_name, cog in sorted(self.bot.cogs.items()):
            if cog_name.startswith("_"):
                continue
            doc = cog.__doc__ or ""
            cmd_count = len([c for c in cog.get_commands() if not c.hidden])
            if cmd_count > 0:
                cog_list.append(f"**{doc.strip() or cog_name}** — `{cmd_count}` commands")

        home.add_field(name="Categories", value="\n".join(cog_list) if cog_list else "No categories", inline=False)
        home.set_footer(text=f"Page 1 | {len(self.bot.commands)} total commands")
        pages.append(home)

        # Category pages
        for cog_name, cog in sorted(self.bot.cogs.items()):
            if cog_name.startswith("_"):
                continue
            cmds = [c for c in cog.get_commands() if not c.hidden]
            if not cmds:
                continue

            em = discord.Embed(
                title=f"{cog.__doc__ or cog_name}",
                colour=discord.Colour.blurple()
            )

            for cmd in sorted(cmds, key=lambda c: c.name):
                aliases = f" (aliases: {', '.join(cmd.aliases)})" if cmd.aliases else ""
                usage = f"`{prefix}{cmd.qualified_name}"
                if cmd.signature:
                    usage += f" {cmd.signature}"
                usage += "`"

                description = cmd.help or cmd.brief or "No description"
                em.add_field(
                    name=f"{usage}{aliases}",
                    value=description[:100],
                    inline=False
                )

            em.set_footer(text=f"Page {len(pages) + 1} | Use {prefix}help <command> for details")
            pages.append(em)

        return pages

    @commands.command(name="help", aliases=["h", "commands"])
    async def help_command(self, ctx: commands.Context, *, command_name: str | None = None):
        """Show help for the bot or a specific command."""
        if command_name:
            cmd = self.bot.get_command(command_name)
            if not cmd:
                await ctx.send(embed=discord.Embed(
                    description=f"❌ Command `{command_name}` not found.",
                    colour=discord.Colour.red()
                ))
                return

            prefix = config["prefix"][0]
            em = discord.Embed(
                title=f"Command: {cmd.qualified_name}",
                colour=discord.Colour.blurple()
            )
            em.add_field(name="Usage", value=f"`{prefix}{cmd.qualified_name} {cmd.signature}`", inline=False)
            if cmd.aliases:
                em.add_field(name="Aliases", value=", ".join(f"`{a}`" for a in cmd.aliases), inline=False)
            if cmd.help:
                em.add_field(name="Description", value=cmd.help, inline=False)

            # Show permissions
            for check in cmd.checks:
                check_name = getattr(check, "__qualname__", "")
                if "has_permissions" in check_name:
                    em.add_field(name="Required Permissions", value="Check command decorators", inline=False)
                    break

            if cmd.cog:
                em.set_footer(text=f"Category: {cmd.cog.__cog_name__}")

            await ctx.send(embed=em)
        else:
            pages = self._build_pages(ctx)
            view = HelpView(pages, ctx.author.id)
            await ctx.send(embed=pages[0], view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(helpCommand(bot))
