import discord, json
from discord.ext import commands
from functions.database_functions import initialize_database

with open('assets/config.json', 'rb') as f:
    config = json.load(f)

EXTENSIONS = [
    'moderation',
    'messageTracker',
    'automod',
    'welcome',
    'logging',
    'fun',
    'utility',
    'roles',
    'tickets',
    'leveling',
    'giveaways',
    'starboard',
    'customcommands',
    'help',
]

class GPDB(commands.Bot):
    async def setup_hook(self):
        """Called once when the bot starts. Initialize database schema."""
        await initialize_database()
        print("Database initialized.")

    async def is_owner(self, user: discord.User):
        return await super().is_owner(user) or user.id in config.get('owners', [])
    
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You lack permissions to use this command!")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Incorrect usage! Missing required argument: `{error.param.name}`")
        elif isinstance(error, commands.CommandNotFound):
            pass  # Silently ignore — custom commands handle this
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(f"I lack the required permissions: `{', '.join(error.missing_permissions)}`")
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send(f"Member not found: `{error.argument}`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"Invalid argument provided! Check command usage.")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"Command on cooldown! Try again in **{error.retry_after:.1f}s**")
        elif isinstance(error, commands.CheckFailure):
            await ctx.send("You don't have permission to use this command!")
        else:
            print(f"Unhandled error in {ctx.command}: {error}")

async def extensions(bot: commands.Bot, mode: str):
    if mode == "load":
        for extension in EXTENSIONS:
            try:
                await bot.load_extension(f"cogs.{extension}")
            except Exception as err:
                print(f"Failed to load {extension}: {err}")
    elif mode == "read":
        return [extension for extension in EXTENSIONS]