import discord, datetime
from discord.ext import commands
from tools.embed import EmbedBuilder

class Member(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        self.poj_cache = {}
    
    @commands.Cog.listener('on_member_remove')
    async def boosterleft(self, before: discord.Member):
        check = await self.bot.db.fetchrow("SELECT role_id FROM booster_roles WHERE guild_id = {} AND user_id = {}".format(before.guild.id, before.id))
        if check:
          role = before.guild.get_role(int(check['role_id']))
          await self.bot.db.execute("DELETE FROM booster_roles WHERE guild_id = {} AND user_id = {}".format(before.guild.id, before.id))
          await role.delete()
    
    @commands.Cog.listener('on_guild_role_delete')
    async def brroledelete(self, role: discord.Role):   
      await self.bot.db.execute("DELETE FROM booster_roles WHERE guild_id = {} AND role_id = {}".format(role.guild.id, role.id)) 

    @commands.Cog.listener('on_member_update')
    async def boosterupdate(self, before: discord.Member, after: discord.Member):
     if before.guild.premium_subscriber_role in before.roles and not before.guild.premium_subscriber_role in after.roles:
        check = await self.bot.db.fetchrow("SELECT role_id FROM booster_roles WHERE guild_id = {} AND user_id = {}".format(before.guild.id, before.id))
        if check:
          role = before.guild.get_role(int(check['role_id']))
          await self.bot.db.execute("DELETE FROM booster_roles WHERE guild_id = {} AND user_id = {}".format(before.guild.id, before.id))
          await role.delete()
    
    @commands.Cog.listener('on_member_join')
    async def auto(self, member: discord.Member):
        role = None
        results = await self.bot.db.fetch("SELECT * FROM autorole WHERE guild_id = {}".format(member.guild.id)) 
        if len(results) == 0: return
        roles = [member.guild.get_role(int(result['role_id'])) for result in results if member.guild.get_role(int(result['role_id'])) is not None and member.guild.get_role(int(result['role_id'])).is_assignable()]
        if role: roles.append(role)
        await member.edit(roles=roles, reason="autorole")
    
    @commands.Cog.listener('on_member_remove')
    async def booster_left(self, member: discord.Member): 
      if member.guild.id == 1132991358022467634:
         if member.guild.premium_subscriber_role in member.roles: 
            check = await self.bot.db.fetchrow("SELECT * FROM donor WHERE user_id = {}".format(member.id))
            if check: await self.bot.db.execute("DELETE FROM donor WHERE user_id = {}".format(member.id))

    @commands.Cog.listener('on_member_update')
    async def booster_unboosted(self, before: discord.Member, after: discord.Member): 
      if before.guild.id == 1132991358022467634:
       if before.guild.premium_subscriber_role in before.roles and not before.guild.premium_subscriber_role in after.roles:
         check = await self.bot.db.fetchrow("SELECT * FROM donor WHERE user_id = {}".format(before.id))
         if check: return await self.bot.db.execute("DELETE FROM donor WHERE user_id = {}".format(before.id))
    
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member): 
     check = await self.bot.db.fetchrow("SELECT * FROM leave WHERE guild_id = $1", member.guild.id)
     if check: 
      channel = member.guild.get_channel(check['channel_id'])
      if channel is None: return 
      try: 
         x=await EmbedBuilder.to_object(EmbedBuilder.embed_replacement(member, check['message']))
         await channel.send(content=x[0],embed=x[1], view=x[2])
      except: await channel.send(EmbedBuilder.embed_replacement(member, check['message'])) 
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member): 
     check = await self.bot.db.fetchrow("SELECT * FROM welcome WHERE guild_id = $1", member.guild.id)
     if check: 
      channel = member.guild.get_channel(check['channel_id'])
      if channel is None: return 
      try: 
         x=await EmbedBuilder.to_object(EmbedBuilder.embed_replacement(member, check['message']))
         await channel.send(content=x[0],embed=x[1], view=x[2])
      except: await channel.send(EmbedBuilder.embed_replacement(member, check['message']))
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot: return   
        results = await self.bot.db.fetch("SELECT * FROM pingonjoin WHERE guild_id = $1", member.guild.id)
        members = [m for m in member.guild.members if (datetime.datetime.now() - m.joined_at.replace(tzinfo=None)).total_seconds() < 180]
        for result in results: 
         channel = member.guild.get_channel(int(result[0]))
         if channel: 
          if len(members) < 10: 
            try: await channel.send(member.mention, delete_after=6)
            except: continue    
          else:           
           if not self.poj_cache.get(str(channel.id)): self.poj_cache[str(channel.id)] = []
           self.poj_cache[str(channel.id)].append(f"{member.mention}")
           if len(self.poj_cache[str(channel.id)]) == 10: 
            try: 
             await channel.send(' '.join([m for m in self.poj_cache[str(channel.id)]]), delete_after=6) 
             self.poj_cache[str(channel.id)] = []
            except:
             self.poj_cache[str(channel.id)] = [] 
             continue
    
    @commands.Cog.listener()
    async def on_member_join(self, before: discord.Member): 
     check = await self.bot.db.fetchrow("SELECT nickname FROM forcenick WHERE user_id = {} AND guild_id = {}".format(before.id, before.guild.id))   
     if check: return await before.edit(nick=check['nickname'])

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
      if str(before.nick) != str(after.nick): 
        check = await self.bot.db.fetchrow("SELECT nickname FROM forcenick WHERE user_id = {} AND guild_id = {}".format(before.id, before.guild.id))   
        if check: return await before.edit(nick=check['nickname'])
    
async def setup(bot):
    await bot.add_cog(Member(bot))