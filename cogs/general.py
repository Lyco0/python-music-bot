import discord
from discord.ext import commands

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping")
    async def ping(self, ctx):
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Bot latency: **{latency}ms**",
            color=0x2ed573 if latency < 100 else 0xffa502 if latency < 200 else 0xff4757
        )
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        await ctx.send(embed=embed)

    @commands.command(name="help_music")
    async def help_music(self, ctx):
        embed = discord.Embed(
            title="🎵 Music Bot Commands",
            description="Here are all the available music commands:",
            color=0x5352ed
        )
        
        commands_list = [
            ("🎵 !play <song/url>", "Play a song or add to queue"),
            ("⏸️ !pause", "Pause current song"),
            ("▶️ !resume", "Resume paused song"),
            ("⏹️ !stop", "Stop and clear queue"),
            ("📋 !queue", "Show current queue"),
            ("✅ !join", "Join your voice channel"),
            ("👋 !leave", "Leave voice channel"),
            ("🏓 !ping", "Check bot latency")
        ]
        
        for name, value in commands_list:
            embed.add_field(name=name, value=value, inline=False)
        
        embed.set_footer(text="Made by Pratik | Use commands responsibly!")
        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(General(bot))