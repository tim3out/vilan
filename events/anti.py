import discord, datetime
from discord.ext import commands

class Anti(commands.Cog):
   def __init__(self, bot: commands.AutoShardedBot):
      self.bot = bot
      self.massjoin_cooldown = 10
      self.massjoin_cache = {}
      self.ban_cache = {}
      self.kick_cache = {}
      self.channel_delete_cache = {}
      self.chanenl_create_cache = {}
      self.role_delete_cache = {}
      self.role_create_cache = {}
    
   async def sendlogs(self, action: str, member: discord.Member, punishment: str): 
    check = await self.bot.db.fetchrow("SELECT logs FROM antinuke_toggle WHERE guild_id = $1", member.guild.id)
    embed = discord.Embed(color=self.bot.color, title=f"{member} punished", description="Was vilan fast? If not, please let us know in https://discord.gg/kQcYeuDjvN").set_thumbnail(url=member.guild.icon).add_field(name="Server", value=member.guild.name).add_field(name="Punishment", value=punishment).add_field(name="Action", value=action)
    if check[0] is None: 
     try: await member.guild.owner.send(embed=embed)
     except: return 
    else:
     channel = member.guild.get_channel(int(check['logs']))
     if channel: await channel.send(embed=embed)
    
   @commands.Cog.listener('on_member_join')
   async def no_avatar(self, member: discord.Member): 
    if not member.avatar: 
        check = await self.bot.db.fetchrow("SELECT * FROM antiraid WHERE command = $1 AND guild_id = $2", "defaultavatar", member.guild.id)
        if check is not None:  
            res1 = await self.bot.db.fetchrow("SELECT * FROM whitelist WHERE guild_id = $1 AND module = $2 AND object_id = $3 AND mode = $4", member.guild.id, "defaultavatar", member.id, "user") 
            if res1: return
            if check['punishment'] == "kick": return await member.kick(reason="AntiRaid: No avatar triggered for this user")
            elif check['punishment'] == "ban": return await member.ban(reason="AntiRaid: No avatar triggered for this user")  
    
   @commands.Cog.listener('on_member_join') 
   async def alt_joined(self, member: discord.Member):  
    check = await self.bot.db.fetchrow("SELECT * FROM antiraid WHERE command = $1 AND guild_id = $2", "newaccounts", member.guild.id)
    if check is not None:
        res1 = await self.bot.db.fetchrow("SELECT * FROM whitelist WHERE guild_id = $1 AND module = $2 AND object_id = $3 AND mode = $4", member.guild.id, "newaccounts", member.id, "user")             
        if res1: return 
        if (datetime.datetime.now() - member.created_at.replace(tzinfo=None)).total_seconds() <= int(check['seconds']):
         if check['punishment'] == "kick": return await member.kick(reason="AntiRaid: Account too young to be allowed")
         elif check['punishment'] == "ban": return await member.ban(reason="AntiRaid: Account too young to be allowed") 
    
   @commands.Cog.listener('on_member_join')
   async def mass_joins(self, member: discord.Member): 
    check = await self.bot.db.fetchrow("SELECT * FROM antiraid WHERE command = $1 AND guild_id = $2", "massjoin", member.guild.id)
    if check: 
      if not self.massjoin_cache.get(str(member.guild.id)): self.massjoin_cache[str(member.guild.id)] = []
      self.massjoin_cache[str(member.guild.id)].append(tuple([datetime.datetime.now(), member.id]))
      expired = [mem for mem in self.massjoin_cache[str(member.guild.id)] if (datetime.datetime.now() - mem[0]).total_seconds() > self.massjoin_cooldown]
      for m in expired: self.massjoin_cache[str(member.guild.id)].remove(m)
      if len(self.massjoin_cache[str(member.guild.id)]) > check['seconds']: 
       members = [me[1] for me in self.massjoin_cache[str(member.guild.id)]] 
       for mem in members:
        if check["punishment"] == "ban": 
         try: await member.guild.ban(user=self.bot.get_user(mem), reason="AntiRaid: Join raid triggered")
         except: continue 
        else: 
          try: await member.guild.kick(user=member.guild.get_member(mem), reason="AntiRaid: Join raid triggered")         
          except: continue
    
   @commands.Cog.listener("on_audit_log_entry_create")
   async def channel_delete(self, entry: discord.AuditLogEntry): 
      if entry.action == discord.AuditLogAction.channel_delete: 
       if entry.guild.owner.id == entry.user.id: return
       if entry.user.top_role.position >= entry.guild.me.top_role.position: return
       check = await self.bot.db.fetchrow("SELECT punishment FROM antinuke WHERE guild_id = $1 AND module = $2", entry.guild.id, "channeldelete")
       if not check: return
       res3 = await self.bot.db.fetchrow("SELECT * FROM whitelist WHERE guild_id = $1 AND module = $2 AND object_id = $3 AND mode = $4", entry.guild.id, "antinuke", entry.user.id, "user")    
       if res3: return 
       if not self.channel_delete_cache.get(str(entry.guild.id)): self.channel_delete_cache[str(entry.guild.id)] = {}
       if not self.channel_delete_cache[str(entry.guild.id)].get(str(entry.user.id)): self.channel_delete_cache[str(entry.guild.id)][str(entry.user.id)] = []
       self.channel_delete_cache[str(entry.guild.id)][str(entry.user.id)].append(datetime.datetime.now())
       expired_cache = [c for c in self.channel_delete_cache[str(entry.guild.id)][str(entry.user.id)] if (datetime.datetime.now() - c).total_seconds() > 60]
       for b in expired_cache: self.channel_delete_cache[str(entry.guild.id)][str(entry.user.id)].remove(b)
       if len(self.channel_delete_cache[str(entry.guild.id)][str(entry.user.id)]) >= check["threshold"]:     
        self.channel_delete_cache[str(entry.guild.id)][str(entry.user.id)] = [] 
        punishment = check["punishment"]
        if punishment == "ban": return await entry.user.ban(reason="AntiNuke: Deleting channels")
        elif punishment == "kick": return await entry.user.kick(reason="AntiNuke: Deleting channels")
        else: 
         await entry.user.edit(roles=[role for role in entry.user.roles if not role.is_assignable() or not self.bot.is_dangerous(role) or role.is_premium_subscriber()], reason="AntiNuke: Deleting channels")
         if entry.user.bot: 
          for role in [r for r in entry.user.roles if r.is_bot_managed()]: await role.edit(permissions=discord.Permissions.none(), reason="AntiNuke: Deleting channels") 
        await self.sendlogs("Deleting channels", entry.user, punishment)
   
   @commands.Cog.listener("on_audit_log_entry_create")
   async def channel_create(self, entry: discord.AuditLogEntry): 
      if entry.action == discord.AuditLogAction.channel_create: 
       if entry.guild.owner.id == entry.user.id: return
       if entry.user.top_role.position >= entry.guild.me.top_role.position: return
       check = await self.bot.db.fetchrow("SELECT punishment FROM antinuke WHERE guild_id = $1 AND module = $2", entry.guild.id, "channelcreate")
       if not check: return
       res3 = await self.bot.db.fetchrow("SELECT * FROM whitelist WHERE guild_id = $1 AND module = $2 AND object_id = $3 AND mode = $4", entry.guild.id, "antinuke", entry.user.id, "user")    
       if res3: return 
       if not self.channel_create_cache.get(str(entry.guild.id)): self.channel_create_cache[str(entry.guild.id)] = {}
       if not self.channel_create_cache[str(entry.guild.id)].get(str(entry.user.id)): self.channel_create_cache[str(entry.guild.id)][str(entry.user.id)] = []
       self.channel_create_cache[str(entry.guild.id)][str(entry.user.id)].append(datetime.datetime.now())
       expired_cache = [c for c in self.channel_create_cache[str(entry.guild.id)][str(entry.user.id)] if (datetime.datetime.now() - c).total_seconds() > 60]
       for b in expired_cache: self.channel_create_cache[str(entry.guild.id)][str(entry.user.id)].remove(b)
       if len(self.channel_create_cache[str(entry.guild.id)][str(entry.user.id)]) >= check["threshold"]:     
        self.channel_create_cache[str(entry.guild.id)][str(entry.user.id)] = [] 
        punishment = check["punishment"]
        if punishment == "ban": return await entry.user.ban(reason="AntiNuke: Creating channels")
        elif punishment == "kick": return await entry.user.kick(reason="AntiNuke: Creating channels")
        else: 
         await entry.user.edit(roles=[role for role in entry.user.roles if not role.is_assignable() or not self.bot.is_dangerous(role) or role.is_premium_subscriber()], reason="AntiNuke: Creating channels")
         if entry.user.bot: 
          for role in [r for r in entry.user.roles if r.is_bot_managed()]: await role.edit(permissions=discord.Permissions.none(), reason="AntiNuke: Creating channels") 
        await self.sendlogs("Creating channels", entry.user, punishment)
   
   @commands.Cog.listener("on_audit_log_entry_create")
   async def role_create(self, entry: discord.AuditLogEntry): 
      if entry.action == discord.AuditLogAction.role_create: 
       if entry.guild.owner.id == entry.user.id: return
       if entry.user.top_role.position >= entry.guild.me.top_role.position: return
       check = await self.bot.db.fetchrow("SELECT punishment FROM antinuke WHERE guild_id = $1 AND module = $2", entry.guild.id, "rolecreate")
       if not check: return
       res3 = await self.bot.db.fetchrow("SELECT * FROM whitelist WHERE guild_id = $1 AND module = $2 AND object_id = $3 AND mode = $4", entry.guild.id, "antinuke", entry.user.id, "user")    
       if res3: return 
       if not self.role_create_cache.get(str(entry.guild.id)): self.role_create_cache[str(entry.guild.id)] = {}
       if not self.role_create_cache[str(entry.guild.id)].get(str(entry.user.id)): self.role_create_cache[str(entry.guild.id)][str(entry.user.id)] = []
       self.role_create_cache[str(entry.guild.id)][str(entry.user.id)].append(datetime.datetime.now())
       expired_cache = [c for c in self.role_create_cache[str(entry.guild.id)][str(entry.user.id)] if (datetime.datetime.now() - c).total_seconds() > 60]
       for b in expired_cache: self.role_create_cache[str(entry.guild.id)][str(entry.user.id)].remove(b)
       if len(self.role_create_cache[str(entry.guild.id)][str(entry.user.id)]) >= check["threshold"]:     
        self.role_create_cache[str(entry.guild.id)][str(entry.user.id)] = [] 
        punishment = check["punishment"]
        if punishment == "ban": return await entry.user.ban(reason="AntiNuke: Creating roles")
        elif punishment == "kick": return await entry.user.kick(reason="AntiNuke: Creating roles")
        else: 
         await entry.user.edit(roles=[role for role in entry.user.roles if not role.is_assignable() or not self.bot.is_dangerous(role) or role.is_premium_subscriber()], reason="AntiNuke: Creating roles")
         if entry.user.bot: 
          for role in [r for r in entry.user.roles if r.is_bot_managed()]: await role.edit(permissions=discord.Permissions.none(), reason="AntiNuke: Creating roles") 
        await self.sendlogs("Creating roles", entry.user, punishment)
   
   @commands.Cog.listener("on_audit_log_entry_create")
   async def role_delete(self, entry: discord.AuditLogEntry): 
      if entry.action == discord.AuditLogAction.role_delete: 
       if entry.guild.owner.id == entry.user.id: return
       if entry.user.top_role.position >= entry.guild.me.top_role.position: return
       check = await self.bot.db.fetchrow("SELECT punishment FROM antinuke WHERE guild_id = $1 AND module = $2", entry.guild.id, "roledelete")
       if not check: return
       res3 = await self.bot.db.fetchrow("SELECT * FROM whitelist WHERE guild_id = $1 AND module = $2 AND object_id = $3 AND mode = $4", entry.guild.id, "antinuke", entry.user.id, "user")    
       if res3: return 
       if not self.role_delete_cache.get(str(entry.guild.id)): self.role_delete_cache[str(entry.guild.id)] = {}
       if not self.role_delete_cache[str(entry.guild.id)].get(str(entry.user.id)): self.role_create_cache[str(entry.guild.id)][str(entry.user.id)] = []
       self.role_delete_cache[str(entry.guild.id)][str(entry.user.id)].append(datetime.datetime.now())
       expired_cache = [c for c in self.role_delete_cache[str(entry.guild.id)][str(entry.user.id)] if (datetime.datetime.now() - c).total_seconds() > 60]
       for b in expired_cache: self.role_delete_cache[str(entry.guild.id)][str(entry.user.id)].remove(b)
       if len(self.role_delete_cache[str(entry.guild.id)][str(entry.user.id)]) >= check["threshold"]:     
        self.role_delete_cache[str(entry.guild.id)][str(entry.user.id)] = [] 
        punishment = check["punishment"]
        if punishment == "ban": return await entry.user.ban(reason="AntiNuke: Deleting roles")
        elif punishment == "kick": return await entry.user.kick(reason="AntiNuke: Deleting roles")
        else: 
         await entry.user.edit(roles=[role for role in entry.user.roles if not role.is_assignable() or not self.bot.is_dangerous(role) or role.is_premium_subscriber()], reason="AntiNuke: Deleting roles")
         if entry.user.bot: 
          for role in [r for r in entry.user.roles if r.is_bot_managed()]: await role.edit(permissions=discord.Permissions.none(), reason="AntiNuke: Deleting roles") 
        await self.sendlogs("Deleting roles", entry.user, punishment)
   
   @commands.Cog.listener("on_audit_log_entry_create")
   async def antibot_join(self, entry: discord.AuditLogEntry):     
    if entry.action == discord.AuditLogAction.bot_add:      
     check = await self.bot.db.fetchrow("SELECT punishment FROM antinuke WHERE guild_id = $1 AND module = $2", entry.guild.id, "antibot")
     if not check: return
     if not entry.target.bot: return      
     res1 = await self.bot.db.fetchrow("SELECT * FROM whitelist WHERE guild_id = $1 AND module = $2 AND object_id = $3 AND mode = $4", entry.guild.id, "antibot", entry.target.id, "user")             
     if res1: return
     res3 = await self.bot.db.fetchrow("SELECT * FROM whitelist WHERE guild_id = $1 AND module = $2 AND object_id = $3 AND mode = $4", entry.guild.id, "antinuke", entry.user.id, "user")    
     if res3: return 
     punishment = check["punishment"]
     await entry.guild.kick(user=entry.target, reason="AntiNuke: Unwhitelisted bot added")
     if entry.guild.owner.id == entry.user.id: return
     if entry.user.top_role.position >= entry.guild.me.top_role.position: return
     if punishment == "ban": return await entry.user.ban(reason="AntiNuke: Added Bots")
     elif punishment == "kick": return await entry.user.kick(reason="AntiNuke: Added Bots")
     else: await entry.user.edit(roles=[role for role in entry.user.roles if not role.is_assignable() or not self.bot.is_dangerous(role) or role.is_premium_subscriber()], reason="AntiNuke: Added Bots")
     await self.sendlogs("Adding Bots", entry.user, punishment)
   
   @commands.Cog.listener("on_audit_log_entry_create")
   async def on_ban(self, entry: discord.AuditLogEntry): 
    if entry.action == discord.AuditLogAction.ban: 
     check = await self.bot.db.fetchrow("SELECT * FROM antinuke WHERE guild_id = $1 AND module = $2", entry.guild.id, "ban")
     if not check: return
     res3 = await self.bot.db.fetchrow("SELECT * FROM whitelist WHERE guild_id = $1 AND module = $2 AND object_id = $3 AND mode = $4", entry.guild.id, "antinuke", entry.user.id, "user")      
     if res3: return 
     if entry.guild.owner.id == entry.user.id: return
     if entry.user.top_role.position >= entry.guild.me.top_role.position: return
     if not self.ban_cache.get(str(entry.guild.id)): self.ban_cache[str(entry.guild.id)] = {}
     if not self.ban_cache[str(entry.guild.id)].get(str(entry.user.id)): self.ban_cache[str(entry.guild.id)][str(entry.user.id)] = [] 
     self.ban_cache[str(entry.guild.id)][str(entry.user.id)].append(datetime.datetime.now())
     expired_bans = [ban for ban in self.ban_cache[str(entry.guild.id)][str(entry.user.id)] if (datetime.datetime.now() - ban).total_seconds() > 60]
     for b in expired_bans: self.ban_cache[str(entry.guild.id)][str(entry.user.id)].remove(b)
     if len(self.ban_cache[str(entry.guild.id)][str(entry.user.id)]) >= check["threshold"]: 
      self.ban_cache[str(entry.guild.id)][str(entry.user.id)] = []
      punishment = check["punishment"]
      if punishment == "ban": return await entry.user.ban(reason="AntiNuke: Banning Members")
      elif punishment == "kick": return await entry.user.kick(reason="AntiNuke: Banning Members")
      else: 
       await entry.user.edit(roles=[role for role in entry.user.roles if not role.is_assignable() or not self.bot.is_dangerous(role) or role.is_premium_subscriber()], reason="AntiNuke: Banning Members")
       if entry.user.bot: 
        for role in [r for r in entry.user.roles if r.is_bot_managed()]: await role.edit(permissions=discord.Permissions.none(), reason="AntiNuke: Banning Members") 
      await self.sendlogs("Banning Members", entry.user, punishment)
   
   @commands.Cog.listener("on_audit_log_entry_create")
   async def on_kick(self, entry: discord.AuditLogEntry): 
    if entry.action == discord.AuditLogAction.kick: 
     check = await self.bot.db.fetchrow("SELECT * FROM antinuke WHERE guild_id = $1 AND module = $2", entry.guild.id, "kick")
     if not check: return
     res3 = await self.bot.db.fetchrow("SELECT * FROM whitelist WHERE guild_id = $1 AND module = $2 AND object_id = $3 AND mode = $4", entry.guild.id, "antinuke", entry.user.id, "ban")      
     if res3: return 
     if entry.guild.owner.id == entry.user.id: return
     if entry.user.top_role.position >= entry.guild.me.top_role.position: return
     if not self.kick_cache.get(str(entry.guild.id)): self.kick_cache[str(entry.guild.id)] = {}
     if not self.kick_cache[str(entry.guild.id)].get(str(entry.user.id)): self.kick_cache[str(entry.guild.id)][str(entry.user.id)] = [] 
     self.kick_cache[str(entry.guild.id)][str(entry.user.id)].append(datetime.datetime.now())
     expired_bans = [ban for ban in self.kick_cache[str(entry.guild.id)][str(entry.user.id)] if (datetime.datetime.now() - ban).total_seconds() > 60]
     for b in expired_bans: self.kick_cache[str(entry.guild.id)][str(entry.user.id)].remove(b)
     if len(self.kick_cache[str(entry.guild.id)][str(entry.user.id)]) >= check["threshold"]: 
      self.kick_cache[str(entry.guild.id)][str(entry.user.id)] = []
      punishment = check["punishment"]
      if punishment == "ban": return await entry.user.ban(reason="AntiNuke: Kicking Members")
      elif punishment == "kick": return await entry.user.kick(reason="AntiNuke: Kicking Members")
      else: 
       await entry.user.edit(roles=[role for role in entry.user.roles if not role.is_assignable() or not self.bot.is_dangerous(role) or role.is_premium_subscriber()], reason="AntiNuke: Kicking Members")
       if entry.user.bot: 
        for role in [r for r in entry.user.roles if r.is_bot_managed()]: await role.edit(permissions=discord.Permissions.none(), reason="AntiNuke: Kicking Members") 
      await self.sendlogs("Kicking Members", entry.user, punishment)

async def setup(bot):
    await bot.add_cog(Anti(bot))