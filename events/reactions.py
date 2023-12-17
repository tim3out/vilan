import discord
from discord.ext import commands

class reactions(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent): 
      if payload.member.bot: return
      if payload.emoji.is_custom_emoji():
       check = await self.bot.db.fetchrow("SELECT role_id FROM reactionrole WHERE guild_id = $1 AND message_id = $2 AND channel_id = $3 AND emoji_id = $4", payload.guild_id, payload.message_id, payload.channel_id, payload.emoji.id)
       if check:
        roleid = check['role_id']
        guild = self.bot.get_guild(payload.guild_id)
        role = guild.get_role(roleid)
        if not role in payload.member.roles: await payload.member.add_roles(role)
      elif payload.emoji.is_unicode_emoji():
        try:
         check = await self.bot.db.fetchrow("SELECT role_id FROM reactionrole WHERE guild_id = $1 AND message_id = $2 AND channel_id = $3 AND emoji_id = $4", payload.guild_id, payload.message_id, payload.channel_id, ord(str(payload.emoji))) 
         if check:
           roleid = check["role_id"]
           guild = self.bot.get_guild(payload.guild_id)
           role = guild.get_role(roleid)
           if not role in payload.member.roles: await payload.member.add_roles(role)      
        except TypeError: pass 

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent): 
     mem = self.bot.get_guild(payload.guild_id).get_member(payload.user_id)
     if not mem: return
     if mem.bot: return 
     if payload.emoji.is_custom_emoji(): 
      check = await self.bot.db.fetchrow("SELECT role_id FROM reactionrole WHERE guild_id = $1 AND message_id = $2 AND channel_id = $3 AND emoji_id = $4", payload.guild_id, payload.message_id, payload.channel_id, payload.emoji.id) 
      if check: 
        roleid = check["role_id"]
        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        role = guild.get_role(int(roleid))
        if role in member.roles: await member.remove_roles(role)
     elif payload.emoji.is_unicode_emoji(): 
      try: 
        check = await self.bot.db.fetchrow("SELECT role_id FROM reactionrole WHERE guild_id = $1 AND message_id = $2 AND channel_id = $3 AND emoji_id = $4", payload.guild_id, payload.message_id, payload.channel_id, ord(str(payload.emoji)))
        if check: 
         roleid = check["role_id"]
         guild = self.bot.get_guild(payload.guild_id)
         member = guild.get_member(payload.user_id)
         role = guild.get_role(int(roleid))
         if role in member.roles: await member.remove_roles(role)
      except TypeError: pass

async def setup(bot):
    await bot.add_cog(reactions(bot))