import discord, os, datetime, asyncio
from discord.ext import commands
from discord.ui import Modal, Select, Button, View
from .predicates import check_vc
from .embed import EmbedBuilder
from .converters import Marry

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

async def make_transcript(c):
   filename = f"{c.name}.txt"
   with open(filename, "w") as file:
    async for msg in c.history(oldest_first=True):
     if not msg.author.bot: file.write(f"{msg.created_at} - {msg.author.display_name}: {msg.clean_content}")
    return filename

class DivorceView(discord.ui.View): 
   def __init__(self, ctx: commands.Context): 
    super().__init__() 
    self.ctx = ctx
    self.status = False

   @discord.ui.button(emoji="<:check:1146359972444254248>")
   async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
    if interaction.user != self.ctx.author: return await interaction.warn("you are not the author of this embed".capitalize())
    check = await interaction.client.db.fetchrow("SELECT * FROM marry WHERE author = $1", self.ctx.author.id)
    if not check:
      check2 = await interaction.client.db.fetchrow("SELECT * FROM marry WHERE soulmate = $1", self.ctx.author.id)
    if not check:
      if check2: await interaction.client.db.execute("DELETE FROM marry WHERE soulmate = $1", self.ctx.author.id)
    elif check: await interaction.client.db.execute("DELETE FROM marry WHERE author = $1", self.ctx.author.id)
    embed = discord.Embed(color=interaction.client.color, description=f"**{self.ctx.author.name}** divorced with their partener")
    await interaction.response.edit_message(content=None, embed=embed, view=None)
    self.status = True              

   @discord.ui.button(emoji="<:stop:1146359810351169609>")
   async def no(self, interaction: discord.Interaction, button: discord.ui.Button): 
     if interaction.user != self.ctx.author: return await self.ctx.bot.ext.warn("you are not the author of this embed".capitalize())
     embe = discord.Embed(color=interaction.client.color, description=f"aborting action....")
     await interaction.response.edit_message(content=None, embed=embe, view=None)
     self.status = True 
   
   async def on_timeout(self) -> None:
       if self.status == False: 
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self) 

class MarryView(discord.ui.View): 
   def __init__(self, ctx: commands.Context, member: discord.Member): 
    super().__init__() 
    self.ctx = ctx 
    self.member = member
    self.status = False 

   @discord.ui.button(emoji="<:check:1146359972444254248>")
   async def yes(self, interaction: discord.Interaction, button: discord.ui.Button): 
    if interaction.user.id == self.ctx.author.id: return await interaction.warn("you can't accept your own marriage".capitalize())
    if not interaction.user == self.member: return await interaction.warn("You are not the author of this embed")
    await interaction.client.db.execute("INSERT INTO marry VALUES ($1,$2,$3)", self.ctx.author.id, self.member.id, datetime.datetime.now().timestamp())      
    embed = discord.Embed(color=interaction.client.color, description=f"**{self.ctx.author}** succesfully married with **{self.member}**")
    await interaction.response.edit_message(content=None, embed=embed, view=None)
    self.status = True              

   @discord.ui.button(emoji="<:stop:1146359810351169609>")
   async def no(self, interaction: discord.Interaction, button: discord.ui.Button): 
     if interaction.user.id == self.ctx.author.id: return await interaction.warn("You can't reject your own marriage")
     if not interaction.user == self.member: return await interaction.warn("You are not the author of this embed")
     embe = discord.Embed(color=interaction.client.color, description=f"Im sorry **{self.ctx.author}**, but **{self.member}** is not the right person for you")
     await interaction.response.edit_message(content=None, embed=embe, view=None)
     self.status = True 
   
   async def on_timeout(self):
     if self.status == False:
      embed = discord.Embed(color=0xa5e9ff, description=f"**{self.member}** failed to reply on time :(")  
      try: await self.message.edit(content=None, embed=embed, view=None)  
      except: pass 

class ClearMod(discord.ui.View): 
  def __init__(self, ctx: commands.Context): 
   super().__init__()
   self.ctx = ctx
   self.status = False

  @discord.ui.button(emoji="<:check:1146359972444254248>")
  async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
   if interaction.user.id != self.ctx.author.id: return await interaction.warn("You are not the author of this embed")
   check = await interaction.client.db.fetchrow("SELECT * FROM mod WHERE guild_id = $1", interaction.guild.id)     
   channelid = check["channel_id"]
   roleid = check["role_id"]
   logsid = check["jail_id"]
   channel = interaction.guild.get_channel(channelid)
   role = interaction.guild.get_role(roleid)
   logs = interaction.guild.get_channel(logsid)
   try: await channel.delete()
   except: pass 
   try: await role.delete()
   except: pass
   try: await logs.delete()
   except: pass 
   await interaction.client.db.execute("DELETE FROM mod WHERE guild_id = $1", interaction.guild.id)
   self.status = True
   return await interaction.response.edit_message(view=None, embed=discord.Embed(color=interaction.client.color, description=f"{interaction.client.yes} {interaction.user.mention}: Moderation module has been disabled"))
  
  @discord.ui.button(emoji="<:stop:1146359810351169609>")
  async def no(self, interaction: discord.Interaction, button: discord.ui.Button): 
    if interaction.user.id != self.ctx.author.id: return await interaction.warn("You are not the author of this embed")
    await interaction.response.edit_message(embed=discord.Embed(color=interaction.client.color, description="aborting action....."), view=None)
    self.status = True

  async def on_timeout(self) -> None:
       if self.status == False: 
        for item in self.children:
            item.disabled = True

        await self.message.edit(view=self)

class CreateTicket(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Create", emoji="🎫", style=discord.ButtonStyle.gray, custom_id="persistent_view:create")
    async def create(self, interaction: discord.Interaction, button: discord.ui.Button):
        check = await interaction.client.db.fetchrow("SELECT * FROM tickets WHERE guild_id = $1", interaction.guild.id)
        if not check: return await interaction.warn("Ticket module is **not** enabled")
        chec = await interaction.client.db.fetchrow("SELECT * FROM opened_tickets WHERE guild_id = $1 AND user_id = $2", interaction.guild.id, interaction.user.id)
        if chec: return await interaction.response.send_message(embed=discord.Embed(color=interaction.client.color, description=f"{interaction.client.warn} {interaction.user.mention}: You already have a ticket opened"), ephemeral=True)
        text = await interaction.guild.create_text_channel(name="ticket-{}".format(interaction.user.name), category=interaction.guild.get_channel(check["category"]) or None)
        overwrites = discord.PermissionOverwrite()
        overwrites.send_messages = True
        overwrites.view_channel = True
        overwrites.attach_files = True
        overwrites.embed_links = True
        await text.set_permissions(interaction.user, overwrite=overwrites)
        if check["opened"]:
         try:
           x = await EmbedBuilder.to_object(EmbedBuilder.embed_replacement(ctx.author, check['opened']))
           message = await channel.send(content=x[0], embed=x[1], view=DeleteTicket())
         except: message = await channel.send(EmbedBuilder.embed_replacement(ctx.author, check['opened']), view=DeleteTicket())
        else:
          embed = discord.Embed(color=interaction.client.color, description="Someone will be with you shortly\nTo close this ticket press <:trash:1145199851613720587>")
          embed.set_footer(text="vilan", icon_url=interaction.client.user.display_avatar.url)
          mes = await text.send(content=f"{interaction.user.mention} welcome", embed=embed, allowed_mentions=discord.AllowedMentions.all(), view=DeleteTicket())
        await interaction.client.db.execute("INSERT INTO opened_tickets VALUES ($1,$2,$3)", interaction.guild.id, text.id, interaction.user.id)
        await interaction.response.send_message(embed=discord.Embed(color=interaction.client.color, description=f"{interaction.client.yes} {interaction.user.mention}: Opened ticket in {text.mention}"), ephemeral=True)
        return

class DeleteTicket(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="", emoji="<:trash:1145199851613720587>", style=discord.ButtonStyle.gray, custom_id="persistent_view:delete")
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
      yes = discord.ui.Button(label="close", style=discord.ButtonStyle.danger)
      no = discord.ui.Button(label="cancel", style=discord.ButtonStyle.gray)
      
      async def yes_callback(inte: discord.Interaction):
          check = await inte.client.db.fetchrow("SELECT logs FROM tickets WHERE guild_id = $1", inte.guild.id)
          if check:
              filename = await make_transcript(interaction.channel)
              embed = discord.Embed(color=inte.client.color, title="ticket logs", description="logs for ticket `{}` | closed by **{}**".format(inte.channel.id, inte.user), timestamp=discord.utils.utcnow())
              try: await inte.guild.get_channel(check["logs"]).send(embed=embed, file=discord.File(filename))
              except: pass
              os.remove(filename)
          await inte.client.db.execute("DELETE FROM opened_tickets WHERE channel_id = $1 AND guild_id = $2", inte.channel.id, inte.guild.id)
          await inte.response.edit_message(content=f"ticket closed by {inte.user.mention}", view=None)
          await asyncio.sleep(2)
          await inte.channel.delete()
          
      yes.callback = yes_callback
      
      async def no_callback(inte: discord.Interaction):
         await inte.response.edit_message(content="aborting action....", view=None)
      
      no.callback = no_callback
        
      view = discord.ui.View()
      view.add_item(yes)
      view.add_item(no)
      await interaction.response.send_message("Are you sure you want to close this ticket?", view=view)

class Transfer(discord.ui.View):
  def __init__(self, ctx: commands.Context, member: discord.Member, amount):
   super().__init__()
   self.member = member
   self.amount = amount
   self.ctx = ctx
   self.status = False
  
  @discord.ui.button(label="", emoji="<:check:1146359972444254248>", style=discord.ButtonStyle.green)
  async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
    if interaction.user.id != self.ctx.author.id: return await interaction.warn("You are not the author of this embed")
    check = await interaction.client.db.fetchrow("SELECT cash FROM economy WHERE user_id = $1", interaction.user.id)
    check2 = await interaction.client.db.fetchrow("SELECT * FROM economy WHERE user_id = $1", self.member.id)
    lol = round(check[0], 2)
    await interaction.client.db.execute("UPDATE economy SET cash = $1 WHERE user_id = $2", lol-self.amount, interaction.user.id)
    await interaction.client.db.execute("UPDATE economy SET cash = $1 WHERE user_id = $2", check2['cash']+self.amount, self.member.id)
    self.status = True
    await interaction.response.edit_message(view=None, embed=discord.Embed(color=interaction.client.color, description=f"{interaction.client.yes} {interaction.user.mention}: transfered **{self.amount}** 💵 to {self.member}"))
  
  @discord.ui.button(label="", emoji="<:stop:1146359810351169609>", style=discord.ButtonStyle.danger)
  async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
    if interaction.user.id != self.ctx.author.id: return await interaction.warn("You are not the author of this embed")
    await interaction.response.edit_message(view=None, embed=discord.Embed(color=interaction.client.color, description="aborting action..."))
    self.status = True
  
  async def on_timeout(self) -> None:
       if self.status == False: 
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self) 

class vcModal(Modal, title="rename your voice channel"):
       name = discord.ui.TextInput(
        label = "voice channel name",
        placeholder = "give your voice channel a better name",
        style = discord.TextStyle.short,
        required = True
       )
        
       async def on_submit(self, interaction: discord.Interaction):
        name = self.name.value
        try:
            await interaction.user.voice.channel.edit(name=name)
            await interaction.approve(f"voice channel renamed to **{name}**")
        except Exception as e: await interaction.error(f"an error occured - {e}")

class vmbuttons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="", emoji=lockemoji, style=discord.ButtonStyle.gray, custom_id="persistent_view:lock")
    async def lock(self, interaction: discord.Interaction, button: discord.ui.Button):
        check = await interaction.client.db.fetchrow("SELECT * FROM voicemaster WHERE guild_id = $1", interaction.guild.id)
        if not check: return await interaction.warn("VoiceMaster is **not** configured")
        elif check:
            channelid = check["channel_id"]
            voicechannel = interaction.guild.get_channel(channelid)
            category = voicechannel.category
            if await check_vc(interaction, category) is False: return
            che = await interaction.client.db.fetchrow("SELECT * FROM vcs WHERE voice = $1 AND user_id = $2", interaction.user.voice.channel.id, interaction.user.id)
            if not che: return await interaction.warn("You don't own this voice channel")
            elif check:
                await interaction.user.voice.channel.set_permissions(interaction.guild.default_role, connect=False)
                await interaction.approve(f"locked <#{interaction.user.voice.channel.id}>")
    
    @discord.ui.button(label="", emoji=unlockemoji, style=discord.ButtonStyle.gray, custom_id="persistent_view:unlock")
    async def unlock(self, interaction: discord.Interaction, button: discord.ui.Button):
        check = await interaction.client.db.fetchrow("SELECT * FROM voicemaster WHERE guild_id = $1", interaction.guild.id)
        if not check: return await interaction.warn("VoiceMaster is **not** configured")
        elif check:
            channelid = check["channel_id"]
            voicechannel = interaction.guild.get_channel(channelid)
            category = voicechannel.category
            if await check_vc(interaction, category) is False: return
            che = await interaction.client.db.fetchrow("SELECT * FROM vcs WHERE voice = $1 AND user_id = $2", interaction.user.voice.channel.id, interaction.user.id)
            if not che: return await interaction.warn("You don't own this voice channel")
            elif check:
                await interaction.user.voice.channel.set_permissions(interaction.guild.default_role, connect=True)
                await interaction.approve(f"unlocked <#{interaction.user.voice.channel.id}>")
    
    @discord.ui.button(label="", emoji=ghostemoji, style=discord.ButtonStyle.gray, custom_id="persistent_view:hide")
    async def hide(self, interaction: discord.Interaction, button: discord.ui.Button):
        check = await interaction.client.db.fetchrow("SELECT * FROM voicemaster WHERE guild_id = $1", interaction.guild.id)
        if not check: return await interaction.warn("VoiceMaster is **not** configured")
        elif check:
            channelid = check["channel_id"]
            voicechannel = interaction.guild.get_channel(channelid)
            category = voicechannel.category
            if await check_vc(interaction, category) is False: return
            che = await interaction.client.db.fetchrow("SELECT * FROM vcs WHERE voice = $1 AND user_id = $2", interaction.user.voice.channel.id, interaction.user.id)
            if not che: return await interaction.warn("You don't own this voice channel")
            elif check:
                await interaction.user.voice.channel.set_permissions(interaction.guild.default_role, view_channel=False)
                await interaction.approve(f"hidden <#{interaction.user.voice.channel.id}>")
    
    @discord.ui.button(label="", emoji=unghostemoji, style=discord.ButtonStyle.gray, custom_id="persistent_view:reveal")
    async def reveal(self, interaction: discord.Interaction, button: discord.ui.Button):
        check = await interaction.client.db.fetchrow("SELECT * FROM voicemaster WHERE guild_id = $1", interaction.guild.id)
        if not check: return await interaction.warn("VoiceMaster is **not** configured")
        elif check:
            channelid = check["channel_id"]
            voicechannel = interaction.guild.get_channel(channelid)
            category = voicechannel.category
            if await check_vc(interaction, category) is False: return
            che = await interaction.client.db.fetchrow("SELECT * FROM vcs WHERE voice = $1 AND user_id = $2", interaction.user.voice.channel.id, interaction.user.id)
            if not che: return await interaction.warn("You don't own this voice channel")
            elif check:
                await interaction.user.voice.channel.set_permissions(interaction.guild.default_role, view_channel=True)
                await interaction.approve(f"revealed <#{interaction.user.voice.channel.id}>")
    
    @discord.ui.button(label="", emoji=channelemoji, style=discord.ButtonStyle.gray, custom_id="persistent_view:rename")
    async def rename(self, interaction: discord.Interaction, button: discord.ui.Button):
        check = await interaction.client.db.fetchrow("SELECT * FROM voicemaster WHERE guild_id = $1", interaction.guild.id)
        if not check: return await interaction.warn("VoiceMaster is **not** configured")
        elif check:
            channelid = check["channel_id"]
            voicechannel = interaction.guild.get_channel(channelid)
            category = voicechannel.category
            if await check_vc(interaction, category) is False: return
            che = await interaction.client.db.fetchrow("SELECT * FROM vcs WHERE voice = $1 AND user_id = $2", interaction.user.voice.channel.id, interaction.user.id)
            if not che: return await interaction.warn("You don't own this voice channel")
            elif check:
                rename = vcModal()
                await interaction.response.send_modal(rename)
    
    @discord.ui.button(label="", emoji=plusemoji, style=discord.ButtonStyle.gray, custom_id="persistent_view:increase")
    async def increase(self, interaction: discord.Interaction, button: discord.ui.Button):
        check = await interaction.client.db.fetchrow("SELECT * FROM voicemaster WHERE guild_id = $1", interaction.guild.id) 
        if not check: return await interaction.warn("VoiceMaster is **not** configured")
        if check is not None:     
             channeid = check["channel_id"]
             voicechannel = interaction.guild.get_channel(channeid)
             category = voicechannel.category 
             if await check_vc(interaction, category) is False: return 
             che = await interaction.client.db.fetchrow("SELECT * FROM vcs WHERE voice = $1 AND user_id = $2", interaction.user.voice.channel.id, interaction.user.id)
             if che is None:
                return await interaction.warn("you don't own this voice channel".capitalize())
             elif che is not None:
              limit = interaction.user.voice.channel.user_limit
              if limit == 99: return await interaction.warn(f"I can't increase the limit for <#{interaction.user.voice.channel.id}>")       
              res = limit + 1
              await interaction.user.voice.channel.edit(user_limit=res)
              await interaction.approve(f"increased <#{interaction.user.voice.channel.id}> limit to **{res}** members")

    @discord.ui.button(label="", emoji=minusemoji, style=discord.ButtonStyle.gray, custom_id="persistent_view:decrease")
    async def decrease(self, interaction: discord.Interaction, button: discord.ui.Button):
        check = await interaction.client.db.fetchrow("SELECT * FROM voicemaster WHERE guild_id = $1", interaction.guild.id)
        if not check: return await interaction.warn("VoiceMaster is **not** configured")
        if check is not None:
             channeid = check["channel_id"]
             voicechannel = interaction.guild.get_channel(channeid)
             category = voicechannel.category 
             if await check_vc(interaction, category) is False: return 
             che = await interaction.client.db.fetchrow("SELECT * FROM vcs WHERE voice = $1 AND user_id = $2", interaction.user.voice.channel.id, interaction.user.id)
             if che is None:
                return await interaction.warn("you don't own this voice channel".capitalize())
             elif che is not None:
              limit = interaction.user.voice.channel.user_limit
              if limit == 0: return await interaction.warn(f"I can't decrease the limit for <#{interaction.user.voice.channel.id}>")       
              res = limit - 1
              await interaction.user.voice.channel.edit(user_limit=res)
              await interaction.approve(f"decreased <#{interaction.user.voice.channel.id}> limit to **{res}** members")
    
    @discord.ui.button(label="", emoji=claimemoji, style=discord.ButtonStyle.gray, custom_id="persistent_view:claim")
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
         check = await interaction.client.db.fetchrow("SELECT * FROM voicemaster WHERE guild_id = $1", interaction.guild.id)
         if not check: return await interaction.warn("VoiceMaster is **not** configured")
         if check is not None:     
             channeid = check["channel_id"]
             voicechannel = interaction.guild.get_channel(channeid)
             category = voicechannel.category 
             if await check_vc(interaction, category) is False: return 
             che = await interaction.client.db.fetchrow("SELECT * FROM vcs WHERE voice = $1", interaction.user.voice.channel.id)           
             memberid = che["user_id"]   
             member = interaction.guild.get_member(memberid)
             if member.id == interaction.user.id: return await interaction.warn("You are already the owner of this voice channel")
             if member in interaction.user.voice.channel.members: return await interaction.warn("The owner of the voice channel is still here")
             else:
                    await interaction.client.db.execute(f"UPDATE vcs SET user_id = $1 WHERE voice = $2", interaction.user.id, interaction.user.voice.channel.id)
                    return await interaction.approve("You are the new owner of this voice channel")     
    
    @discord.ui.button(label="", emoji=manemoji, style=discord.ButtonStyle.gray, custom_id="persistent_view:info")
    async def info(self, interaction: discord.Interaction, button: discord.ui.Button):
         check = await interaction.client.db.fetchrow("SELECT * FROM voicemaster WHERE guild_id = $1", interaction.guild.id)
         if not check: return await interaction.warn("VoiceMaster is **not** configured")
         if not interaction.user.voice: return await interaction.warn("You are not in a voice channel")
         if check is not None:     
             che = await interaction.client.db.fetchrow("SELECT * FROM vcs WHERE voice = $1", interaction.user.voice.channel.id)
             if che is not None:
                memberid = che["user_id"]   
                member = interaction.guild.get_member(memberid)
                embed = discord.Embed(color=interaction.client.color, title=interaction.user.voice.channel.name, description=f"owner: **{member}** (`{member.id}`)\ncreated: **{discord.utils.format_dt(interaction.user.voice.channel.created_at, style='R')}**\nbitrate: **{interaction.user.voice.channel.bitrate/1000}kbps**\nconnected: **{len(interaction.user.voice.channel.members)} member{'s' if len(interaction.user.voice.channel.members) > 1 else ''}**")    
                embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar)
                embed.set_thumbnail(url=member.display_avatar)
                await interaction.response.send_message(embed=embed, view=None, ephemeral=True)                     
    @discord.ui.button(label="", emoji=hammeremoji, style=discord.ButtonStyle.gray, custom_id="persistent_view:manage")
    async def manage(self, interaction: discord.Interaction, button: discord.ui.Button):
         check = await interaction.client.db.fetchrow("SELECT * FROM voicemaster WHERE guild_id = $1", interaction.guild.id)
         if not check: return await interaction.warn("VoiceMaster is **not** configured")
         if check is not None:     
            channeid = check["channel_id"]
            voicechannel = interaction.guild.get_channel(channeid)
            category = voicechannel.category 
            if await check_vc(interaction, category) is False: return 
            che = await interaction.client.db.fetchrow("SELECT * FROM vcs WHERE voice = $1 AND user_id = $2", interaction.user.voice.channel.id, interaction.user.id)
            if che is None: return await interaction.warn("you don't own this voice channel".capitalize())
            if len(interaction.user.voice.channel.members) == 1: return await interaction.warn("You are the only person in this channel")
            em = discord.Embed(color=interaction.client.color, title="VoiceMaster Moderation Menu", description="Moderate your voice channel using the options below")
            options = [ 
               discord.SelectOption(
                  label="mute",
                  description="mute member in the voice channel",
                  emoji="<:muted:1130421571778007082>"
               ),
               discord.SelectOption(
                  label="unmute",
                  description="unmute members in the voice channel",
                  emoji="<:unmuted:1130421375081910402>"
               ),
               discord.SelectOption(
                  label="deafen",
                  description="deafen members in your voice channel",
                  emoji="<:deafened:1130421608977289299>"
               ),
               discord.SelectOption(
                  label="undeafen",
                  emoji="<:undeafened:1130421530170499093>",
                  description="undeafen members in your voice channel"
               ),
               discord.SelectOption(
                  label="kick",
                  description="kick members from your voice channel",
                  emoji="<:hammer:1145199036425584701>"
               )
            ]
            select = discord.ui.Select(options=options, placeholder="select category...")
            members = []
            for member in interaction.user.voice.channel.members:
               if member.id == interaction.user.id: continue
               members.append(discord.SelectOption(label=member.name, value=member.id))

            async def select_callback(interactio: discord.Interaction):
               if select.values[0] == "mute":
                  e = discord.Embed(color=interaction.client.color, title="VoiceMaster Moderation | Mute Members", description="mute members in your voice channel")
                  sel = Select(options=members, placeholder="select members...", min_values=1, max_values=len(members))
                  async def sel_callback(interacti: discord.Interaction):
                    for s in sel.values: 
                     await interacti.guild.get_member(int(s)).edit(mute=True, reason=f"muted by {interacti.user}")

                    embede = discord.Embed(color=interaction.client.color, description="{} {}: Muted all members".format(interaction.client.yes, interacti.user.mention))   
                    await interacti.response.edit_message(embed=embede, view=None)

                  sel.callback = sel_callback 
                  
                  vi = View()
                  vi.add_item(sel)
                  await interactio.response.send_message(embed=e, view=vi, ephemeral=True) 

               elif select.values[0] == "unmute":
                  e = discord.Embed(color=interaction.client.color, title="VoiceMaster Moderation | Unmute Members", description="unmute members in your voice channel")
                  sel = Select(options=members, placeholder="select members...", min_values=1, max_values=len(members))
                  async def sel_callback(interacti: discord.Interaction):
                    for s in sel.values: 
                     await interacti.guild.get_member(int(s)).edit(mute=False, reason=f"unmuted by {interacti.user}")

                    embede = discord.Embed(color=interaction.client.color, description="{} {}: Unuted all members".format(interaction.client.yes, interacti.user.mention))   
                    await interacti.response.edit_message(embed=embede, view=None)

                  sel.callback = sel_callback 
                  
                  vi = View()
                  vi.add_item(sel)
                  await interactio.response.send_message(embed=e, view=vi, ephemeral=True)    

               if select.values[0] == "deafen":
                  e = discord.Embed(color=interaction.client.color, title="VoiceMaster Moderation | Deafen Members", description="deafen members in your voice channel")
                  sel = Select(options=members, placeholder="select members...", min_values=1, max_values=len(members))
                  async def sel_callback(interacti: discord.Interaction):
                    for s in sel.values: 
                     await interacti.guild.get_member(int(s)).edit(deafen=True, reason=f"deafened by {interacti.user}")

                    embede = discord.Embed(color=interaction.client.color, description="{} {}: Deafened all members".format(interaction.client.yes, interacti.user.mention))   
                    await interacti.response.edit_message(embed=embede, view=None)

                  sel.callback = sel_callback 
                  
                  vi = View()
                  vi.add_item(sel)
                  await interactio.response.send_message(embed=e, view=vi, ephemeral=True) 

               elif select.values[0] == "undeafen":
                  e = discord.Embed(color=interaction.client.color, title="VoiceMaster Moderation | Undeafen Members", description="undeafen members in your voice channel")
                  sel = Select(options=members, placeholder="select members...", min_values=1, max_values=len(members))
                  async def sel_callback(interacti: discord.Interaction):
                    for s in sel.values: 
                     await interacti.guild.get_member(int(s)).edit(deafen=False, reason=f"undeafened by {interacti.user}")

                    embede = discord.Embed(color=interaction.client.color, description="{} {}: Undeafened all members".format(interaction.client.yes, interacti.user.mention))   
                    await interacti.response.edit_message(embed=embede, view=None)

                  sel.callback = sel_callback 
                  
                  vi = View()
                  vi.add_item(sel)
                  await interactio.response.send_message(embed=e, view=vi, ephemeral=True)    
               
               elif select.values[0] == "kick":
                  e = discord.Embed(color=interaction.client.color, title="VoiceMaster Moderation | Kick Members", description="kick members from your voice channel")
                  sel = Select(options=members, placeholder="select members...", min_values=1, max_values=len(members))
                  async def sel_callback(interacti: discord.Interaction):
                    for s in sel.values: 
                     await interacti.guild.get_member(int(s)).move_to(channel=None, reason="kicked by {}".format(interacti.user))

                    embede = discord.Embed(color=interaction.client.color, description="{} {}: Kicked all members".format(interaction.client.yes, interacti.user.mention))   
                    await interacti.response.edit_message(embed=embede, view=None)

                  sel.callback = sel_callback 
                  
                  vi = View()
                  vi.add_item(sel)
                  await interactio.response.send_message(embed=e, view=vi, ephemeral=True) 

            select.callback = select_callback
            
            view = View()
            view.add_item(select)
            await interaction.response.send_message(embed=em, view=view, ephemeral=True)