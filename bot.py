import discord
from discord.ext import commands
import asyncio
import logging
from dotenv import load_dotenv
import os


load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f"Ready, {bot.user.name}")

@bot.command()
async def load(ctx, extension):
    await bot.load_extension(f"cogs.{extension}")
    await ctx.send(f"Loaded {extension} done.")

@bot.command()
async def unload(ctx, extension):
    await bot.unload_extension(f"cogs.{extension}")
    await ctx.send(f"Unloaded {extension} done.")

@bot.command()
async def reload(ctx, extension):
    await bot.reload_extension(f"cogs.{extension}")
    await ctx.send(f"Reloaded {extension} done.")

async def load_extensions():
    for filename in os.listdir("./cogs"):
        print("Found in cogs:", filename)  # ← debug
        if filename.endswith(".py"):
            ext = f"cogs.{filename[:-3]}"
            print("Loading:", ext)          # ← debug
            await bot.load_extension(ext)


async def main() -> None:
    
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[handler],
        format="%(asctime)s:%(levelname)s:%(name)s: %(message)s"
    )

    await load_extensions()

    async with bot:
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())