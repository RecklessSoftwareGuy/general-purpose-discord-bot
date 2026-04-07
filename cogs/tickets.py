import discord
from discord.ext import commands
from functions import database_functions as db
from functions import ticket_functions as tf
from views import embeds, views


class ticketCommands(commands.Cog):
    """🎫 Support ticket system."""
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # Register persistent views
        self.bot.add_view(views.TicketPanelView())
        self.bot.add_view(views.TicketControlView())
        print(f"Initialized: {self.__cog_name__}")
        super().__init__()

    @commands.group(name="ticket", invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def ticket(self, ctx: commands.Context):
        """Ticket system commands."""
        em = discord.Embed(
            title="🎫 Ticket Commands",
            description=(
                "`ticket setup` — Send the ticket panel\n"
                "`ticket setcategory <category>` — Set ticket category\n"
                "`ticket setlog <channel>` — Set ticket log channel\n"
                "`ticket close` — Close the current ticket\n"
                "`ticket add <user>` — Add a user to this ticket\n"
                "`ticket remove <user>` — Remove a user from this ticket\n"
            ),
            colour=discord.Colour.blurple()
        )
        await ctx.send(embed=em)

    @ticket.command(name="setup")
    @commands.has_permissions(manage_guild=True)
    async def ticket_setup(self, ctx: commands.Context):
        """Send the ticket panel in the current channel."""
        await ctx.send(embed=embeds.ticket_panel_x0(), view=views.TicketPanelView())
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

    @ticket.command(name="setcategory")
    @commands.has_permissions(manage_guild=True)
    async def ticket_setcategory(self, ctx: commands.Context, category: discord.CategoryChannel):
        """Set the category where tickets are created."""
        if ctx.guild:
            await db.update_guild_config(ctx.guild.id, ticket_category_id=category.id)
            await ctx.send(embed=embeds.config_set_x0("Ticket Category", category.name))

    @ticket.command(name="setlog")
    @commands.has_permissions(manage_guild=True)
    async def ticket_setlog(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the channel where ticket transcripts are sent."""
        if ctx.guild:
            await db.update_guild_config(ctx.guild.id, ticket_log_channel_id=channel.id)
            await ctx.send(embed=embeds.config_set_x0("Ticket Log Channel", channel.mention))

    @ticket.command(name="close")
    async def ticket_close(self, ctx: commands.Context):
        """Close the current ticket."""
        if not ctx.guild or not isinstance(ctx.channel, discord.TextChannel):
            return
        ticket_data = await db.get_ticket(ctx.channel.id)
        if not ticket_data:
            await ctx.send(embed=embeds.error_x0("This is not a ticket channel."))
            return

        if not isinstance(ctx.author, discord.Member):
            return
        if ctx.author.id != ticket_data["user_id"] and not ctx.author.guild_permissions.manage_guild:
            await ctx.send(embed=embeds.error_x0("Only the ticket creator or staff can close this."))
            return

        await ctx.send(embed=embeds.ticket_closed_x0(ctx.author))
        transcript = await tf.close_ticket_channel(ctx.channel, ctx.author)

        config = await db.get_guild_config(ctx.guild.id)
        if config and config.get("ticket_log_channel_id"):
            log_ch = ctx.guild.get_channel(config["ticket_log_channel_id"])
            if log_ch and isinstance(log_ch, discord.TextChannel):
                try:
                    await log_ch.send(
                        f"🎫 Ticket `#{ctx.channel.name}` closed by {ctx.author.mention}",
                        file=discord.File(transcript, filename=f"transcript-{ctx.channel.name}.txt")
                    )
                except discord.Forbidden:
                    pass

        import asyncio
        await asyncio.sleep(3)
        try:
            await ctx.channel.delete(reason="Ticket closed")
        except discord.Forbidden:
            pass

    @ticket.command(name="add")
    async def ticket_add(self, ctx: commands.Context, user: discord.Member):
        """Add a user to the current ticket."""
        if isinstance(ctx.channel, discord.TextChannel):
            ticket_data = await db.get_ticket(ctx.channel.id)
            if not ticket_data:
                await ctx.send(embed=embeds.error_x0("This is not a ticket channel."))
                return
            await ctx.channel.set_permissions(user, view_channel=True, send_messages=True)
            await ctx.send(embed=embeds.success_x0(f"Added {user.mention} to the ticket."))

    @ticket.command(name="remove")
    async def ticket_remove(self, ctx: commands.Context, user: discord.Member):
        """Remove a user from the current ticket."""
        if isinstance(ctx.channel, discord.TextChannel):
            ticket_data = await db.get_ticket(ctx.channel.id)
            if not ticket_data:
                await ctx.send(embed=embeds.error_x0("This is not a ticket channel."))
                return
            await ctx.channel.set_permissions(user, overwrite=None)
            await ctx.send(embed=embeds.success_x0(f"Removed {user.mention} from the ticket."))


async def setup(bot: commands.Bot):
    await bot.add_cog(ticketCommands(bot))
