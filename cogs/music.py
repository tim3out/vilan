import discord, pomice, async_timeout, asyncio, typing
from discord.ext import commands

class music(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
    
    async def start_nodes(self):
      await self.bot.wait_until_ready()
      try:
        self.bot.node = await pomice.NodePool().create_node(bot=self.bot, host="lavalink.ordinaryender.my.eu.org", port=443, password="ordinarylavalink", identifier="MAIN", spotify_client_id="5326b2423b684c9eb64d7b8191ea5091", spotify_client_secret="b260e252dd134c829f8ede5e21975bb0", secure=True, apple_music=True)
      except pomice.NodeConnectionFailure: pass
    
    async def get_player(self, ctx: commands.Context, *, connect: bool = True):
      if not hasattr(self.bot, "node"): raise commands.BadArgument("No nodes available")
      if not ctx.author.voice: raise commands.BadArgument("You're not **connected** to a voice channel")
      if ctx.guild.me.voice and ctx.guild.me.voice.channel != ctx.author.voice.channel: raise commands.BadArgument("I'm **already** connected to a voice channel")
      if (player := self.bot.node.get_player(ctx.guild.id)) is None or not ctx.guild.me.voice:
        if not connect: raise commands.BadArgument("I'm not **connected** to a voice channel")
        else:
          await ctx.author.voice.channel.connect(cls=Player, self_deaf=True)
          player = self.bot.node.get_player(ctx.guild.id)
          player.invoke_id = ctx.channel.id
          await player.set_volume(65)

      return player
    
    @commands.Cog.listener()
    async def on_pomice_track_end(self, player: pomice.Player, track: pomice.Track, reason: str):
        await player.next()
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
      player = self.bot.node.get_player(member.guild.id)
      if before.channel:
       if member.guild.me in before.channel.members:
          if len(before.channel.members) == 1:
             await player.destroy()
    
    @commands.command(description="play a song", usage="[song]", help="music")
    async def play(self, ctx: commands.Context, *, song: str):
        player: Player = await self.get_player(ctx)
        result = await player.get_tracks(query=song, ctx=ctx)
        if not result: return await ctx.awrn("Cannot find any **tracks** with the name **{song}**")
        if isinstance(result, pomice.Playlist):
          for track in result.tracks:
            await player.insert(track)
        else:
            track = result[0]
            await player.insert(track)
            if player.is_playing: 
                await ctx.neutral(f"Added [{track.title}]({track.uri}) to the queue", emoji="🎵")
      
        if not player.is_playing:
            await player.next()
    
    @commands.command(description="skip the song", help="music")
    async def skip(self, ctx: commands.Context):
        player: Player = await self.get_player(ctx, connect=False)
        if player.is_playing:
            await ctx.neutral("Skipped the song", emoji="🎵")
            await player.skip()
        else:
            await ctx.warn("There is nothing playing")
    
    @commands.command(description="set a loop for the track", usage="[type]\ntype: off, track", help="music")
    async def loop(self, ctx: commands.Context, option: typing.Literal["track", "off"]):
        player: Player = await self.get_player(ctx, connect=False)
        if option == "off":
            if not player.loop:
                return await ctx.warn("**Loop** is not set")
        elif option == "track":
            if not player.is_playing:
                return await ctx.warn("The are no **tracks** playing")
        
        await ctx.neutral(f"**{option}** looping the queue", emoji="🎵")
        await player.set_loop(option if option != "off" else False)

    @commands.command(description="pause the player", help="music")
    async def pause(self, ctx: commands.Context):
        player: Player = await self.get_player(ctx, connect=False)
        if player.is_playing and not player.is_paused:
            await ctx.neutral("Paused the player", emoji="🎵")
            await player.set_pause(True)
        else:
            await ctx.warn("There are **tracks** playing")

    @commands.command(description="resume the player", help="music")
    async def resume(self, ctx: commands.Context):
        player: Player = await self.get_player(ctx, connect=False)
        if player.is_playing and player.is_paused:
            await ctx.neutral("Resumed the player", emoji="🎵")
            await player.set_pause(False)
        else:
            await ctx.warn("There are no **tracks** playing")

    @commands.command(description="set player volume", usage="[volume]", help="music")
    async def volume(self, ctx: commands.Context, vol: int):
        player: Player = await self.get_player(ctx, connect=False)
        if not 0 <= vol <= 150:
            return await ctx.warn("Volume should be between **0** and **150**")
        await player.set_volume(vol)
        await ctx.neutral(f"Volume set to **{vol}**", emoji="🎵")

    @commands.command(description="stop the player", aliases=["dc"], help="music")
    async def stop(self, ctx: commands.Context):
        player: Player = await self.get_player(ctx, connect=False)
        await player.teardown()
        await ctx.neutral("Stopped the player", emoji="🎵")
    
async def setup(bot):
    await bot.add_cog(music(bot))

class Player(pomice.Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.invoke_id: int = None
        self.track: pomice.Track = None
        self.queue: asyncio.Queue = asyncio.Queue()
        self.waiting: bool = False
        self.loop: str = False

    async def play(self, track: pomice.Track):
        await super().play(track)

    async def insert(self, track: pomice.Track):
        await self.queue.put(track)

        return True

    async def next(self, no_vc: bool = False):
        if no_vc:
            if self.is_playing or self.waiting: return
        
        self.waiting = True
        if self.loop == "track" and self.track:
            track = self.track
        else:
            track = await self.queue.get()

        await self.play(track)
        self.track = track
        self.waiting = False
        if (channel := self.guild.get_channel(self.invoke_id)):
            await channel.send(embed=discord.Embed(color=self.bot.color, description=f"🎵 {track.requester.mention}: Now Playing [{track.title}]({track.uri})"))

        return track

    async def skip(self):
        if self.is_paused:
            await self.set_pause(False)

        return await self.stop()

    async def set_loop(self, state: str):
        self.loop = state

    async def teardown(self):
        try:
            self.queue._queue.clear()
            await self.destroy()
        except:
            pass