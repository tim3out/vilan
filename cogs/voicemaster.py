import discord
from discord.ext import commands
from tools.views import vmbuttons
from tools.predicates import check_owner
from tools.views import vmbuttons

lockemoji = "<:lock:1145187811016855582>"
unlockemoji = "<:unlock:1145198392176283750>"
ghostemoji = "<:ghost:1145195437884715078>"
unghostemoji = "<:unghost:1145193149044621342>"
channelemoji = "<:channel:1145188250273726464>"
plusemoji = "<:plus:1145187023251058769>"
minusemoji = "<:minus:1145188572685680641>"
claimemoji = "<:claim:1145186153385959546>"
manemoji = "<:man:1145241989957296159>"
hammeremoji = "<:hammer:1145199036425584701>"

class voicemaster(commands.Cog):
   def __init__(self, bot: commands.AutoShardedBot):
       self.bot = bot
   
   def create_interface(self, ctx: commands.Context) -> discord.Embed: 
    em = discord.Embed(color=self.bot.color, title="VoiceMaster Interface", description="use the buttons below to control the voice channel")    
    em.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
    em.add_field(name="Manage", value=f"{lockemoji} - [`lock`](https://discord.gg/DX4MxrxsCg) the voice channel\n{unlockemoji} - [`unlock`](https://discord.gg/DX4MxrxsCg) the voice channel\n{ghostemoji} - [`hide`](https://discord.gg/DX4MxrxsCg) the voice channel\n{unghostemoji} - [`reveal`](https://discord.gg/DX4MxrxsCg) the voice channel\n{channelemoji} - [`rename`](https://discord.gg/DX4MxrxsCg) the voice channel")
    em.add_field(name="Misc", value=f"{plusemoji} - [`increase`](https://discord.gg/DX4MxrxsCg) the user limit\n{minusemoji} - [`decrease`](https://discord.gg/DX4MxrxsCg) the user limit\n{claimemoji} - [`claim`](https://discord.gg/DX4MxrxsCg) the voice channel\n{manemoji} - [`info`](https://discord.gg/DX4MxrxsCg) of the channel\n{hammeremoji} - [`manage`](https://discord.gg/DX4MxrxsCg) the voice channel")
    return em

   async def vm_channels(self, channel: discord.VoiceChannel, member: discord.Member) -> bool: 
     if len(channel.category.channels) == 50: 
      await member.move_to(channel=None)
      try: 
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label=f"sent from {member.guild.name}", disabled=True)) 
        await member.send("I couldn't make a new voice channel", view=view)
      except: pass 
     return len(channel.category.channels) == 50
   
   async def vm_overwrites(self, channel: discord.VoiceChannel, member: discord.Member) -> bool:  
     if member.bot: return
     che = await self.bot.db.fetchrow("SELECT * FROM vcs WHERE voice = $1", channel.id)
     if che: 
      if che['user_id'] == member.id: return
      if channel.overwrites_for(channel.guild.default_role).connect == False: 
       if member not in channel.overwrites and member.id != member.guild.owner_id:
         if not channel.overwrites_for(member).connect == True:
          try: return await member.move_to(channel=None, reason="member not allowed to join this voice channel")
          except: pass
    
   @commands.Cog.listener() 
   async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
     check = await self.bot.db.fetchrow("SELECT * FROM voicemaster WHERE guild_id = $1", member.guild.id)
     if check:
      jtc = int(check["channel_id"])
      if not before.channel and after.channel: 
       if after.channel.id == jtc: 
        if await self.vm_channels(after.channel, member) is True: return
        channel = await member.guild.create_voice_channel(name=f"{member.name}'s channel", category=after.channel.category, reason="creating temporary voice channel")
        await channel.set_permissions(member.guild.default_role, connect=True)
        await member.move_to(channel=channel)
        return await self.bot.db.execute("INSERT INTO vcs VALUES ($1,$2)", member.id, channel.id)
       else: return await self.vm_channels(after.channel, member)    
      elif before.channel and after.channel: 
       if before.channel.id == jtc: return 
       if before.channel.category == after.channel.category: 
        if after.channel.id == jtc: 
         che = await self.bot.db.fetchrow("SELECT * FROM vcs WHERE voice = $1", before.channel.id)
         if che: 
           if len(before.channel.members) == 0: return await member.move_to(channel=before.channel) 
         if await self.vm_channels(after.channel, member) is True: return
         cha = await member.guild.create_voice_channel(name=f"{member.name}'s channel", category=after.channel.category, reason="creating temporary voice channel")
         await cha.set_permissions(member.guild.default_role, connect=True)
         await member.move_to(channel=cha)
         return await self.bot.db.execute("INSERT INTO vcs VALUES ($1,$2)", member.id, cha.id)  
        elif before.channel.id != after.channel.id: 
         await self.vm_channels(after.channel, member)
         che = await self.bot.db.fetchrow("SELECT * FROM vcs WHERE voice = $1", before.channel.id)
         if che: 
           if len(before.channel.members) == 0:
            await self.bot.db.execute("DELETE FROM vcs WHERE voice = $1", before.channel.id)
            await before.channel.delete(reason="no one in the temporary voice channel")                
       else: 
        if after.channel.id == jtc: 
         if await self.vm_channels(after.channel, member) is True: return
         cha = await member.guild.create_voice_channel(name=f"{member.name}'s channel", category=after.channel.category, reason="creating temporary voice channel")
         await cha.set_permissions(member.guild.default_role, connect=True)
         await member.move_to(channel=cha)
         return await self.bot.db.execute("INSERT INTO vcs VALUES ($1,$2)", member.id, cha.id)
        else:
          await self.vm_channels(after.channel, member)
          result = await self.bot.db.fetchrow("SELECT * FROM vcs WHERE voice = $1", before.channel.id)
          if result: 
            if len(before.channel.members) == 0:
             await self.bot.db.execute("DELETE FROM vcs WHERE voice = $1", before.channel.id)
             return await before.channel.delete(reason="no one in the temporary voice channel")        
      elif before.channel and not after.channel: 
       if before.channel.id == jtc: return
       che = await self.bot.db.fetchrow("SELECT * FROM vcs WHERE voice = $1", before.channel.id)
       if che: 
           if len(before.channel.members) == 0:
            await self.bot.db.execute("DELETE FROM vcs WHERE voice = $1", before.channel.id)
            await before.channel.delete(reason="no one in the temporary voice channel")    
   
   @commands.group(aliases=["vc"], invoke_without_command=True)
   async def voice(self, ctx):
    await ctx.create_pages()
   
   @voice.command(description="lock the voice channel", help="voicemaster")
   @check_owner()
   async def lock(self, ctx: commands.Context): 
      await ctx.author.voice.channel.set_permissions(ctx.guild.default_role, connect=False)
      return await ctx.approve(f"locked <#{ctx.author.voice.channel.id}>")

   @voice.command(description="unlock the voice channel", help="voicemaster")
   @check_owner()
   async def unlock(self, ctx: commands.Context):  
      await ctx.author.voice.channel.set_permissions(ctx.guild.default_role, connect=True)
      return await ctx.approve(f"unlocked <#{ctx.author.voice.channel.id}>")
   
   @voice.command(description="rename the voice channel", usage="[name]", help="voicemaster")
   @check_owner()
   async def rename(self, ctx: commands.Context, *, name: str): 
      await ctx.author.voice.channel.edit(name=name)
      return await ctx.approve(f"voice channel renamed to **{name}**")
   
   @voice.command(description="hide the voice channel", help="voicemaster")
   @check_owner()
   async def hide(self, ctx: commands.Context): 
      await ctx.author.voice.channel.set_permissions(ctx.guild.default_role, view_channel=False)
      return await ctx.approve(f"hidden <#{ctx.author.voice.channel.id}>")   

   @voice.command(description="reveal the voice channel", help="voicemaster")
   @check_owner()
   async def reveal(self, ctx: commands.Context): 
      await ctx.author.voice.channel.set_permissions(ctx.guild.default_role, view_channel=True)
      return await ctx.approve(f"revealed <#{ctx.author.voice.channel.id}>")
   
   @commands.command(description="get an updated version of the voice master interface", help="voicemaster")
   @commands.has_permissions("administrator")
   async def interface(self, ctx: commands.Context):
     check = await self.bot.db.fetchrow("SELECT * FROM voicemaster WHERE guild_id = $1", ctx.guild.id)
     if not check: return await ctx.warn("VoiceMaster is **not** configured")
     await ctx.send(embed=self.create_interface(ctx), view=vmbuttons())
     await ctx.message.delete()
   
   @commands.group(invoke_without_command=True, aliases=["vm"])
   async def voicemaster(self, ctx):
    await ctx.create_pages()
   
   @voicemaster.command(description="configure voicemaster module for your server", help="voicemaster")
   @commands.has_permissions("administrator")
   async def setup(self, ctx: commands.Context):
      check = await self.bot.db.fetchrow("SELECT * FROM voicemaster WHERE guild_id = $1", ctx.guild.id)
      if check: return await ctx.warn("VoiceMaster is **already** configured")
      elif not check:
        category = await ctx.guild.create_category("voice channels")
        overwrite = {ctx.guild.default_role: discord.PermissionOverwrite(send_messages=False)}
        text = await ctx.guild.create_text_channel("interface", overwrites=overwrite, category=category)
        vc = await ctx.guild.create_voice_channel("Join to Create", category=category)
        await text.send(embed=self.create_interface(ctx), view=vmbuttons())
        await self.bot.db.execute("INSERT INTO voicemaster VALUES ($1,$2,$3)", ctx.guild.id, vc.id, text.id)
        return await ctx.approve("Configured voicemaster")
   
   @voicemaster.command(description="remove voicemaster module from your server", help="voicemaster", aliases=["unsetup"])
   @commands.has_permissions("administrator")
   async def remove(self, ctx):
      check = await self.bot.db.fetchrow("SELECT * FROM voicemaster WHERE guild_id = $1", ctx.guild.id)
      if not check: return await ctx.warn("VoiceMaster is **not** configured")
      elif check:
        try:
            channelid = check["channel_id"]
            interfaceid = check["interface"]
            channel2 = ctx.guild.get_channel(interfaceid)
            channel = ctx.guild.get_channel(channelid)
            category = channel.category
            channels = category.channels
            for chan in channels:
                try: await chan.delete()
                except: continue
            
            await category.delete()
            await channel2.delete()
            await self.bot.db.execute("DELETE FROM voicemaster WHERE guild_id = $1", ctx.guild.id)
            await ctx.approve("VoiceMaster has been deleted")
        except:
            await self.bot.db.execute("DELETE FROM voicemaster WHERE guild_id = $1", ctx.guild.id)
            await ctx.approve("VoiceMaster has been deleted")
   
   voicemaster.command()
   @commands.is_owner()
   async def view(self, ctx):
        await ctx.send(embed=self.create_interface(ctx), view=vmbuttons())
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(voicemaster(bot))