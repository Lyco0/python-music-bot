import discord
from discord.ext import commands
import yt_dlp
import asyncio

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.music_queue = {}
        self.is_paused = {}
        
        self.youtube_dl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0'
        }
        
        self.ffmpeg_opts = {
            'options': '-vn'
        }
        
        self.ytdl = yt_dlp.YoutubeDL(self.youtube_dl_opts)

    async def play_next(self, ctx):
        guild_id = ctx.guild.id
        if guild_id in self.music_queue and self.music_queue[guild_id]:
            url = self.music_queue[guild_id].pop(0)
            await self.play_song(ctx, url)
        else:
            embed = discord.Embed(
                title="🎵 Queue Empty",
                description="No more songs in queue. Disconnecting...",
                color=0xff6b6b
            )
            await ctx.send(embed=embed)
            voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            if voice_client:
                await voice_client.disconnect()

    async def play_song(self, ctx, url):
        try:
            voice_channel = ctx.author.voice.channel
        except AttributeError:
            embed = discord.Embed(
                title="❌ Error",
                description="You need to be in a voice channel to use this command!",
                color=0xff4757
            )
            await ctx.send(embed=embed)
            return

        try:
            voice_client = await voice_channel.connect()
        except discord.ClientException:
            voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            if voice_client is None:
                embed = discord.Embed(
                    title="❌ Connection Error",
                    description="I am not connected to a voice channel.",
                    color=0xff4757
                )
                await ctx.send(embed=embed)
                return

        try:
            # Show loading message
            loading_embed = discord.Embed(
                title="🔄 Loading...",
                description="Fetching audio data, please wait...",
                color=0xffa502
            )
            loading_msg = await ctx.send(embed=loading_embed)

            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(url, download=False))

            if 'entries' in data:
                data = data['entries'][0]

            filename = data['url']
            player = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(filename, **self.ffmpeg_opts))

            def after_playing(error):
                if not self.is_paused.get(ctx.guild.id, False):
                    coroutine = self.play_next(ctx)
                    future = asyncio.run_coroutine_threadsafe(coroutine, self.bot.loop)
                    try:
                        future.result()
                    except:
                        pass

            voice_client.play(player, after=after_playing)
            
            # Update loading message with success
            success_embed = discord.Embed(
                title="🎵 Now Playing",
                description=f"**{data['title']}**",
                color=0x2ed573
            )
            success_embed.add_field(
                name="Duration", 
                value=f"{data.get('duration', 'Unknown')} seconds" if data.get('duration') else "Unknown",
                inline=True
            )
            success_embed.add_field(
                name="Requested by", 
                value=ctx.author.mention,
                inline=True
            )
            if data.get('thumbnail'):
                success_embed.set_thumbnail(url=data['thumbnail'])
            
            success_embed.set_footer(text=f"Playing in {voice_channel.name}")
            await loading_msg.edit(embed=success_embed)

        except Exception as e:
            print(f"Error playing song: {e}")
            error_embed = discord.Embed(
                title="❌ Playback Error",
                description=f"An error occurred while playing the song:\n```{str(e)[:100]}...```",
                color=0xff4757
            )
            await ctx.send(embed=error_embed)

    @commands.command(name="play")
    async def play(self, ctx, *, query):
        if "youtube.com" in query or "youtu.be" in query:
            query = query.split("&feature=")[0]

        guild_id = ctx.guild.id
        if guild_id not in self.music_queue:
            self.music_queue[guild_id] = []

        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice_client and voice_client.is_playing():
            self.music_queue[guild_id].append(query)
            embed = discord.Embed(
                title="➕ Added to Queue",
                description=f"**{query}**",
                color=0x5352ed
            )
            embed.add_field(name="Position", value=f"#{len(self.music_queue[guild_id])}", inline=True)
            embed.add_field(name="Requested by", value=ctx.author.mention, inline=True)
            embed.set_footer(text=f"Queue length: {len(self.music_queue[guild_id])}")
            await ctx.send(embed=embed)
        else:
            await self.play_song(ctx, query)

    @commands.command(name="join")
    async def join(self, ctx):
        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            embed = discord.Embed(
                title="❌ Error",
                description="You need to be in a voice channel!",
                color=0xff4757
            )
            await ctx.send(embed=embed)
            return
            
        if ctx.voice_client is not None:
            embed = discord.Embed(
                title="🔄 Moved",
                description=f"Moved to **{channel.name}**",
                color=0x3742fa
            )
            await ctx.send(embed=embed)
            return await ctx.voice_client.move_to(channel)

        await channel.connect()
        embed = discord.Embed(
            title="✅ Joined",
            description=f"Connected to **{channel.name}**",
            color=0x2ed573
        )
        await ctx.send(embed=embed)

    @commands.command(name="leave")
    async def leave(self, ctx):
        if ctx.voice_client is None:
            embed = discord.Embed(
                title="❌ Error",
                description="Not connected to any voice channel.",
                color=0xff4757
            )
            return await ctx.send(embed=embed)

        channel_name = ctx.voice_client.channel.name
        await ctx.voice_client.disconnect()
        
        embed = discord.Embed(
            title="👋 Disconnected",
            description=f"Left **{channel_name}**",
            color=0xff6b6b
        )
        await ctx.send(embed=embed)

    @commands.command(name="pause")
    async def pause(self, ctx):
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            self.is_paused[ctx.guild.id] = True  # Mark as paused
            embed = discord.Embed(
                title="⏸️ Paused",
                description="Music has been paused",
                color=0xffa502
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ Nothing Playing",
                description="Nothing is currently playing.",
                color=0xff4757
            )
            await ctx.send(embed=embed)

    @commands.command(name="resume")
    async def resume(self, ctx):
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            self.is_paused[ctx.guild.id] = False  # Mark as not paused
            embed = discord.Embed(
                title="▶️ Resumed",
                description="Music has been resumed",
                color=0x2ed573
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ Nothing Paused",
                description="Nothing is currently paused.",
                color=0xff4757
            )
            await ctx.send(embed=embed)

    @commands.command(name="stop")
    async def stop(self, ctx):
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice_client and voice_client.is_playing():
            voice_client.stop()
            guild_id = ctx.guild.id
            self.is_paused[guild_id] = False
        
            if guild_id in self.music_queue:
                queue_length = len(self.music_queue[guild_id])
                self.music_queue[guild_id] = []
            else:
                queue_length = 0
            
            embed = discord.Embed(
                title="⏹️ Stopped",
                description="Music stopped and queue cleared",
                color=0xff6b6b
            )
            if queue_length > 0:
                embed.add_field(name="Queue Cleared", value=f"{queue_length} songs removed", inline=True)
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ Nothing Playing",
                description="Nothing is currently playing.",
                color=0xff4757
            )
            await ctx.send(embed=embed)

    @commands.command(name="queue")
    async def queue(self, ctx):
        guild_id = ctx.guild.id
        if guild_id in self.music_queue and self.music_queue[guild_id]:
            embed = discord.Embed(
                title="📋 Music Queue",
                color=0x5352ed
            )
            
            queue_list = []
            for i, url in enumerate(self.music_queue[guild_id][:10]):  # Show first 10
                queue_list.append(f"`{i + 1}.` {url}")
            
            embed.description = "\n".join(queue_list)
            
            if len(self.music_queue[guild_id]) > 10:
                embed.add_field(
                    name="And more...", 
                    value=f"+{len(self.music_queue[guild_id]) - 10} more songs",
                    inline=False
                )
            
            embed.set_footer(text=f"Total: {len(self.music_queue[guild_id])} songs")
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="📋 Queue Empty",
                description="No songs in queue",
                color=0x747d8c
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Music(bot))