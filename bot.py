import discord
from discord.ext import commands
import yt_dlp  # Changed import
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
BOT_PREFIX = "!"
intents = discord.Intents.default()
intents.voice_states = True
intents.message_content = True
bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

youtube_dl_opts = {
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

ffmpeg_opts = {
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(youtube_dl_opts)

music_queue = {}


async def play_next(ctx):
    guild_id = ctx.guild.id
    if guild_id in music_queue and music_queue[guild_id]:
        url = music_queue[guild_id].pop(0)
        await play_song(ctx, url)
    else:
        await ctx.send("Queue is empty. Stopping playback.")
        voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        if voice_client:
            await voice_client.disconnect()


async def play_song(ctx, url):
    try:
        voice_channel = ctx.author.voice.channel
    except AttributeError:
        await ctx.send("You need to be in a voice channel to use this command.")
        return

    try:
        voice_client = await voice_channel.connect()
    except discord.ClientException:
        voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        if voice_client is None:
            await ctx.send("I am not connected to a voice channel.")
            return

    try:
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url']
        player = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(filename, **ffmpeg_opts))

        def after_playing(error):
            coroutine = play_next(ctx)
            future = asyncio.run_coroutine_threadsafe(coroutine, bot.loop)
            try:
                future.result()
            except:
                pass

        voice_client.play(player, after=after_playing)
        await ctx.send(f"Now playing: {data['title']}")

    except Exception as e:
        print(f"Error playing song: {e}")
        await ctx.send(f"An error occurred while playing the song: {e}")


@bot.command(name="play")
async def play(ctx, *, query):
    if "youtube.com" in query or "youtu.be" in query:
        query = query.split("&feature=")[0]

    guild_id = ctx.guild.id
    if guild_id not in music_queue:
        music_queue[guild_id] = []

    if discord.utils.get(bot.voice_clients, guild=ctx.guild) and discord.utils.get(bot.voice_clients,
                                                                                      guild=ctx.guild).is_playing():
        music_queue[guild_id].append(query)
        await ctx.send("Added to queue!")
    else:
        await play_song(ctx, query)


@bot.command(name="join")
async def join(ctx):
    channel = ctx.author.voice.channel
    if ctx.voice_client is not None:
        return await ctx.voice_client.move_to(channel)

    await channel.connect()


@bot.command(name="leave")
async def leave(ctx):
    if ctx.voice_client is None:
        return await ctx.send("Not connected to any voice channel.")

    await ctx.voice_client.disconnect()


@bot.command(name="pause")
async def pause(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await ctx.send("Paused.")


@bot.command(name="resume")
async def resume(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await ctx.send("Resumed.")


@bot.command(name="stop")
async def stop(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        guild_id = ctx.guild.id
        if guild_id in music_queue:
            music_queue[guild_id] = []
        await ctx.send("Stopped.")


@bot.command(name="queue")
async def queue(ctx):
    guild_id = ctx.guild.id
    if guild_id in music_queue and music_queue[guild_id]:
        queue_str = "\n".join([f"{i + 1}. {url}" for i, url in enumerate(music_queue[guild_id])])
        await ctx.send(f"Queue:\n{queue_str}")
    else:
        await ctx.send("The queue is empty.")


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} ({bot.user.id})")
    print("------")


@bot.command(name="ping")
async def ping(ctx):
    await ctx.send("Pong!")


bot.run(TOKEN)