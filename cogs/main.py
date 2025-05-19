import discord
from discord.ext import commands

class Main(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="test", help="Check if Main cog is loaded.")
    async def test(self, ctx: commands.Context):
        await ctx.send(f"Main loaded")


async def setup(bot: commands.Bot):
    await bot.add_cog(Main(bot))

        