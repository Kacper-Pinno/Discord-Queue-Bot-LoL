import discord
from discord.ext import commands
import os
from config import DISCORD_API_KEY

intents = discord.Intents.default()
intents.typing = False
intents.presences = False

bot = commands.Bot(command_prefix='/', help_command=None, intents = discord.Intents.all())  #   Command Prefix + Bot Permissions set



@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def setup_hook():
    await bot.load_extension("cogs.verification")
    await bot.tree.sync()  # <- Force sync slash commands
    


bot.run(DISCORD_API_KEY) # Run the bot