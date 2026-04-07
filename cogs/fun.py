import discord, random, aiohttp
from discord.ext import commands
from views import embeds


EIGHT_BALL_RESPONSES = [
    "It is certain.", "It is decidedly so.", "Without a doubt.",
    "Yes — definitely.", "You may rely on it.", "As I see it, yes.",
    "Most likely.", "Outlook good.", "Yes.", "Signs point to yes.",
    "Reply hazy, try again.", "Ask again later.", "Better not tell you now.",
    "Cannot predict now.", "Concentrate and ask again.",
    "Don't count on it.", "My reply is no.", "My sources say no.",
    "Outlook not so good.", "Very doubtful.",
]

RPS_CHOICES = ["rock", "paper", "scissors"]
RPS_EMOJIS = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}


class funCommands(commands.Cog):
    """🎮 Fun and entertainment commands."""
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.session: aiohttp.ClientSession | None = None
        print(f"Initialized: {self.__cog_name__}")
        super().__init__()

    async def cog_load(self):
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        if self.session:
            await self.session.close()

    @commands.command(name="8ball", aliases=["eightball"])
    async def eightball(self, ctx: commands.Context, *, question: str):
        """Ask the magic 8-ball a question."""
        answer = random.choice(EIGHT_BALL_RESPONSES)
        await ctx.send(embed=embeds.eightball_x0(question, answer))

    @commands.command(name="coinflip", aliases=["flip", "coin"])
    async def coinflip(self, ctx: commands.Context):
        """Flip a coin."""
        result = random.choice(["Heads", "Tails"])
        emoji = "🪙"
        em = discord.Embed(description=f"{emoji} **{result}!**", colour=discord.Colour.gold())
        await ctx.send(embed=em)

    @commands.command(name="roll", aliases=["dice"])
    async def roll(self, ctx: commands.Context, sides: int = 6, count: int = 1):
        """Roll dice. Usage: roll [sides] [count]"""
        if sides < 2 or count < 1 or count > 25:
            await ctx.send(embed=embeds.error_x0("Invalid parameters! Sides ≥ 2, count 1-25."))
            return
        results = [random.randint(1, sides) for _ in range(count)]
        result_text = ", ".join(f"**{r}**" for r in results)
        total = sum(results)
        em = discord.Embed(
            title=f"🎲 Rolling {count}d{sides}",
            description=f"Results: {result_text}\n**Total: {total}**",
            colour=discord.Colour.purple()
        )
        await ctx.send(embed=em)

    @commands.command(name="rps")
    async def rps(self, ctx: commands.Context, choice: str):
        """Play rock-paper-scissors. Usage: rps rock/paper/scissors"""
        choice = choice.lower()
        if choice not in RPS_CHOICES:
            await ctx.send(embed=embeds.error_x0("Choose `rock`, `paper`, or `scissors`!"))
            return

        bot_choice = random.choice(RPS_CHOICES)

        if choice == bot_choice:
            result = "It's a **tie**! 🤝"
            colour = discord.Colour.yellow()
        elif (choice == "rock" and bot_choice == "scissors") or \
             (choice == "paper" and bot_choice == "rock") or \
             (choice == "scissors" and bot_choice == "paper"):
            result = "You **win**! 🎉"
            colour = discord.Colour.green()
        else:
            result = "You **lose**! 😢"
            colour = discord.Colour.red()

        em = discord.Embed(
            title="Rock Paper Scissors",
            description=f"You: {RPS_EMOJIS[choice]} **{choice.capitalize()}**\nBot: {RPS_EMOJIS[bot_choice]} **{bot_choice.capitalize()}**\n\n{result}",
            colour=colour
        )
        await ctx.send(embed=em)

    @commands.command(name="meme")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def meme(self, ctx: commands.Context):
        """Get a random meme from Reddit."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        try:
            async with self.session.get("https://meme-api.com/gimme") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    em = discord.Embed(
                        title=data.get("title", "Meme"),
                        colour=discord.Colour.random(),
                        url=data.get("postLink", "")
                    )
                    em.set_image(url=data.get("url", ""))
                    em.set_footer(text=f"👍 {data.get('ups', 0)} | r/{data.get('subreddit', 'memes')}")
                    await ctx.send(embed=em)
                else:
                    await ctx.send(embed=embeds.error_x0("Couldn't fetch a meme. Try again later!"))
        except Exception:
            await ctx.send(embed=embeds.error_x0("Failed to fetch meme. API may be down."))

    @commands.command(name="joke")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def joke(self, ctx: commands.Context):
        """Get a random joke."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        try:
            async with self.session.get("https://official-joke-api.appspot.com/random_joke") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    em = discord.Embed(
                        title="😂 Joke",
                        description=f"**{data['setup']}**\n\n||{data['punchline']}||",
                        colour=discord.Colour.random()
                    )
                    await ctx.send(embed=em)
                else:
                    await ctx.send(embed=embeds.error_x0("Couldn't fetch a joke. Try again!"))
        except Exception:
            await ctx.send(embed=embeds.error_x0("Failed to fetch joke. API may be down."))

    @commands.command(name="poll")
    async def poll(self, ctx: commands.Context, *, question: str):
        """Create a simple yes/no poll. Usage: poll <question>"""
        em = embeds.poll_x0(question, ctx.author)
        msg = await ctx.send(embed=em)
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")

    @commands.command(name="avatar", aliases=["av", "pfp"])
    async def avatar(self, ctx: commands.Context, user: discord.Member | discord.User | None = None):
        """Display a user's avatar."""
        target = user or ctx.author
        em = discord.Embed(
            title=f"{target.display_name}'s Avatar",
            colour=discord.Colour.blurple()
        )
        em.set_image(url=target.display_avatar.url)
        em.set_footer(text=f"Requested by {ctx.author.display_name}")
        await ctx.send(embed=em)

    @commands.command(name="banner")
    async def banner(self, ctx: commands.Context, user: discord.Member | discord.User | None = None):
        """Display a user's banner."""
        target = user or ctx.author
        # Need to fetch the user to get banner
        fetched = await self.bot.fetch_user(target.id)
        if fetched.banner:
            em = discord.Embed(
                title=f"{target.display_name}'s Banner",
                colour=discord.Colour.blurple()
            )
            em.set_image(url=fetched.banner.url)
            await ctx.send(embed=em)
        else:
            await ctx.send(embed=embeds.error_x0(f"{target.display_name} doesn't have a banner."))

    @commands.command(name="emojify")
    async def emojify(self, ctx: commands.Context, *, text: str):
        """Convert text to regional indicator emojis."""
        result = []
        for char in text.lower():
            if char.isalpha():
                result.append(f":regional_indicator_{char}:")
            elif char == " ":
                result.append("   ")
            elif char.isdigit():
                digit_words = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
                result.append(f":{digit_words[int(char)]}:")
            else:
                result.append(char)

        output = " ".join(result)
        if len(output) > 2000:
            await ctx.send(embed=embeds.error_x0("Text is too long to emojify!"))
        else:
            await ctx.send(output)

    @commands.command(name="choose", aliases=["pick"])
    async def choose(self, ctx: commands.Context, *, choices: str):
        """Choose between multiple options. Separate with | or ,"""
        separator = "|" if "|" in choices else ","
        options = [o.strip() for o in choices.split(separator) if o.strip()]
        if len(options) < 2:
            await ctx.send(embed=embeds.error_x0("Provide at least 2 choices separated by `|` or `,`!"))
            return
        choice = random.choice(options)
        em = discord.Embed(
            title="🤔 I choose...",
            description=f"**{choice}**",
            colour=discord.Colour.purple()
        )
        await ctx.send(embed=em)

    @commands.command(name="rate")
    async def rate(self, ctx: commands.Context, *, thing: str):
        """Rate something out of 10."""
        rating = random.randint(0, 10)
        bar = "█" * rating + "░" * (10 - rating)
        em = discord.Embed(
            title="⭐ Rating",
            description=f"I rate **{thing}** a **{rating}/10**!\n{bar}",
            colour=discord.Colour.gold()
        )
        await ctx.send(embed=em)


async def setup(bot: commands.Bot):
    await bot.add_cog(funCommands(bot))
