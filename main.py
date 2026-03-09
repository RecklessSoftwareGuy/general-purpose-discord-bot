import discord, json
from discord.ext import commands
from assets import protocols

with open('assets/config.json', 'rb') as f:
    config = json.load(f)

bot = protocols.GPDB(command_prefix=commands.when_mentioned_or(*config["prefix"]), case_insensitive=True, help_command=None, intents=discord.Intents.all())

@bot.listen('on_ready')
async def ready():
    await protocols.extensions(bot, "load")
    print(f"\n{bot.user.display_name} is online!") #type: ignore


@bot.command(name="ping")
async def network_round_trip_latency(ctx: commands.Context):
    await ctx.send(f"Pong! **{int(bot.latency * 1000)}ms**")


bot.run(token=config["token"])