import discord
from discord.ext import commands
from functions import database_functions as db
from views import embeds


class messageTracker(commands.Cog):
    """📨 Message tracking, snipe, and message utilities."""
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # Cache for snipe and editsnipe (per channel)
        self._deleted_messages: dict[int, discord.Message] = {}
        self._edited_messages: dict[int, tuple[discord.Message, discord.Message]] = {}
        print(f"Initialized: {self.__cog_name__}")
        super().__init__()

    @commands.Cog.listener(name="on_message")
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if message.guild:
            await db.record_user_messages(message.author.id, message.guild.id)

    @commands.Cog.listener(name="on_message_delete")
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot:
            return
        self._deleted_messages[message.channel.id] = message

    @commands.Cog.listener(name="on_message_edit")
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot:
            return
        if before.content != after.content:
            self._edited_messages[before.channel.id] = (before, after)

    @commands.command(name="message_info", aliases=['mprofile'])
    async def message_info(self, ctx: commands.Context, user: discord.Member | discord.User | None = None):
        if user is None:
            user = ctx.author
        if ctx.guild:
            userData = {
                "username": user.global_name or user.name,
                "joinDate": user.joined_at if isinstance(user, discord.Member) else None,
                "createdAt": user.created_at,
                "nMessages": await db.read_user_messages(user.id, ctx.guild.id),
                "authorname": ctx.author.global_name or ctx.author.name,
                "authorAvatar": ctx.author.avatar,
                "servername": ctx.guild.name,
                "serverIcon": ctx.guild.icon,
            }
            await ctx.reply(embed=embeds.mprofile_x0(userData))

    @commands.command(name="snipe")
    async def snipe(self, ctx: commands.Context):
        """Show the last deleted message in this channel."""
        message = self._deleted_messages.get(ctx.channel.id)
        if not message:
            await ctx.send(embed=embeds.error_x0("Nothing to snipe! No recently deleted messages."))
            return
        await ctx.send(embed=embeds.snipe_x0(message))

    @commands.command(name="editsnipe", aliases=["esnipe"])
    async def editsnipe(self, ctx: commands.Context):
        """Show the last edited message in this channel."""
        data = self._edited_messages.get(ctx.channel.id)
        if not data:
            await ctx.send(embed=embeds.error_x0("Nothing to snipe! No recently edited messages."))
            return
        before, after = data
        await ctx.send(embed=embeds.editsnipe_x0(before, after))

    @commands.command(name="pin_message", aliases=["pin"])
    @commands.has_permissions(manage_messages=True)
    async def pin_message(self, ctx: commands.Context):
        if ctx.message.reference:
            messageId = ctx.message.reference.message_id
            if messageId:
                message = await ctx.channel.fetch_message(messageId)
                if message:
                    try:
                        await message.pin()
                        await ctx.send(embed=embeds.success_x0(f"📌 Message pinned!"))
                    except Exception:
                        await ctx.reply(embed=embeds.error_x0("Unable to pin message!"))
                    return
        await ctx.reply(embed=embeds.error_x0("Reply to a message to pin it!"))

    @commands.command(name="unpin")
    @commands.has_permissions(manage_messages=True)
    async def unpin_message(self, ctx: commands.Context):
        """Unpin a message by replying to it."""
        if ctx.message.reference:
            messageId = ctx.message.reference.message_id
            if messageId:
                message = await ctx.channel.fetch_message(messageId)
                if message and message.pinned:
                    try:
                        await message.unpin()
                        await ctx.send(embed=embeds.success_x0("📌 Message unpinned!"))
                    except Exception:
                        await ctx.reply(embed=embeds.error_x0("Unable to unpin message!"))
                    return
        await ctx.reply(embed=embeds.error_x0("Reply to a pinned message to unpin it!"))


async def setup(bot: commands.Bot):
    await bot.add_cog(messageTracker(bot))