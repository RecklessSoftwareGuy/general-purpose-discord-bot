import discord, json
from discord.ext import commands

with open('assets/config.json', 'rb') as f:
    config = json.load(f)

class GPDB(commands.Bot):
    async def is_owner(self, user: discord.User):
        return await super().is_owner(user) or user.id in config['owners']
    
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You lack permissions to use this command!")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Incorrect usage! Missing required argument(s)!")
        elif isinstance(error, commands.CommandNotFound):
            await ctx.send("Command not found!")
        else:
            print(f"Unhandled error: {error}")
    
async def extensions(bot: commands.Bot, mode: str):
    extensions = ['moderation', 'messageTracker']
    if mode == "load":
        for extension in extensions:
            try:
                await bot.load_extension(f"cogs.{extension}")
            except Exception as err:
                print(err)
    elif mode == "read":

        return [extension for extension in extensions]