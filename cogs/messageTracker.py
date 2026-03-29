import discord
from discord.ext import commands
from functions import database_functions as df
from views import embeds

class messageTracker(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()

    @commands.Cog.listener(name="on_message")
    async def on_message(self, message: discord.Message):
        if message.guild:
            await df.record_user_messages(message.author.id, message.guild.id)
        await self.bot.process_commands(message)
    
    @commands.command(name="message_info", aliases=['mprofile'])
    async def message_info(self, ctx: commands.Context, user: discord.Member | discord.User | None = None):
        if user is None:
            user = ctx.author
        if ctx.guild:
            userData = {
                "username" : user.global_name,
                "joinDate" : user.joined_at, #type: ignore
                "createdAt" : user.created_at,
                "nMessages" : await df.read_user_messages(user.id, ctx.guild.id),
                "lastOnline" : 0, #Feature to be added
                "authorname" : ctx.author.global_name,
                "authorAvatar" : ctx.author.avatar, #type: ignore
                "servername" : ctx.guild.name,
                "serverIcon" : ctx.guild.icon,
            }
            await ctx.reply(embed=embeds.mprofile_x0(userData))
        return
    
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
                    except:
                        await ctx.reply("Unable to pin message!")
                    return
        await ctx.reply("Unable to pin message!")

async def setup(bot: commands.Bot):
    await bot.add_cog(messageTracker(bot))