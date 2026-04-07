import discord, time
from discord.ext import commands, tasks
from functions import database_functions as db
from functions import giveaway_functions as gf
from functions import utility_functions as uf
from views import embeds


class giveawayCommands(commands.Cog):
    """🎉 Giveaway system."""
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.check_giveaways.start()
        print(f"Initialized: {self.__cog_name__}")
        super().__init__()

    def cog_unload(self):
        self.check_giveaways.cancel()

    @tasks.loop(seconds=15)
    async def check_giveaways(self):
        """Check for ended giveaways."""
        ended = await db.get_active_giveaways()
        for g in ended:
            winners, message = await gf.end_giveaway_flow(self.bot, g)
            if winners and message:
                winner_text = ", ".join(w.mention for w in winners)
                try:
                    await message.reply(f"🎉 Congratulations {winner_text}! You won **{g['prize']}**!")
                except discord.HTTPException:
                    pass

    @check_giveaways.before_loop
    async def before_check_giveaways(self):
        await self.bot.wait_until_ready()

    @commands.group(name="giveaway", aliases=["gw"], invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def giveaway(self, ctx: commands.Context):
        """Giveaway commands."""
        em = discord.Embed(
            title="🎉 Giveaway Commands",
            description=(
                "`giveaway start <duration> <winners> <prize>` — Start a giveaway\n"
                "`giveaway end <message_id>` — End a giveaway early\n"
                "`giveaway reroll <message_id>` — Re-roll a giveaway winner\n"
            ),
            colour=discord.Colour.gold()
        )
        await ctx.send(embed=em)

    @giveaway.command(name="start")
    @commands.has_permissions(manage_guild=True)
    async def giveaway_start(self, ctx: commands.Context, duration: str, winners: int, *, prize: str):
        """Start a giveaway. Usage: giveaway start 1d 1 Nitro"""
        td = uf.parse_duration(duration)
        if not td:
            await ctx.send(embed=embeds.error_x0("Invalid duration! Use `1d`, `12h`, `1w`, etc."))
            return

        if winners < 1 or winners > 20:
            await ctx.send(embed=embeds.error_x0("Winners must be between 1 and 20."))
            return

        end_time = int(time.time() + td.total_seconds())

        em = embeds.giveaway_x0(prize, ctx.author, end_time, winners)
        msg = await ctx.send(embed=em)
        await msg.add_reaction("🎉")

        await db.create_giveaway(
            ctx.guild.id, ctx.channel.id, msg.id,  # type: ignore
            ctx.author.id, prize, winners, end_time
        )

    @giveaway.command(name="end")
    @commands.has_permissions(manage_guild=True)
    async def giveaway_end(self, ctx: commands.Context, message_id: int):
        """End a giveaway early by message ID."""
        giveaway_data = await db.get_giveaway_by_message(message_id)
        if not giveaway_data or giveaway_data["ended"]:
            await ctx.send(embed=embeds.error_x0("Giveaway not found or already ended."))
            return

        winners, message = await gf.end_giveaway_flow(self.bot, giveaway_data)
        if winners and message:
            winner_text = ", ".join(w.mention for w in winners)
            await message.reply(f"🎉 Congratulations {winner_text}! You won **{giveaway_data['prize']}**!")
        await ctx.send(embed=embeds.success_x0("Giveaway ended!"))

    @giveaway.command(name="reroll")
    @commands.has_permissions(manage_guild=True)
    async def giveaway_reroll(self, ctx: commands.Context, message_id: int):
        """Re-roll a giveaway winner."""
        giveaway_data = await db.get_giveaway_by_message(message_id)
        if not giveaway_data:
            await ctx.send(embed=embeds.error_x0("Giveaway not found."))
            return

        if not ctx.guild:
            return
        channel = ctx.guild.get_channel(giveaway_data["channel_id"])
        if not channel or not isinstance(channel, discord.TextChannel):
            await ctx.send(embed=embeds.error_x0("Giveaway channel not found."))
            return

        winners = await gf.pick_winners(channel, message_id, giveaway_data["winners"])
        if winners:
            winner_text = ", ".join(w.mention for w in winners)
            await ctx.send(f"🎉 New winner(s): {winner_text}! Congratulations!")
        else:
            await ctx.send(embed=embeds.error_x0("No valid entries to re-roll."))


async def setup(bot: commands.Bot):
    await bot.add_cog(giveawayCommands(bot))
