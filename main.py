import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Debug: Check if token is loaded
if TOKEN is None:
    print("ERROR: DISCORD_TOKEN not found in .env file!")
    exit(1)

BOT_PREFIX = "!"

intents = discord.Intents.default()
intents.voice_states = True
intents.message_content = True

class MusicBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=BOT_PREFIX, intents=intents)
        
    async def on_ready(self):
        print(f"Logged in as {self.user.name} ({self.user.id})")
        print("------")

    async def setup_hook(self):
        # Load all cogs
        await self.load_extension('cogs.music')
        await self.load_extension('cogs.general')

if __name__ == "__main__":
    bot = MusicBot()
    bot.run(TOKEN)