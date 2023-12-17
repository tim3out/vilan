import discord, math, asyncio
from discord.ext import commands
from tools.predicates import server_owner, is_level
from discord.ext.commands import Author

class Leveling(commands.Cog): 
  def __init__(self, bot: commands.AutoShardedBot): 
   self.bot = bot 
   self._cd = commands.CooldownMapping.from_cooldown(3, 5, commands.BucketType.member) 

  def get_ratelimit(self, message):
        bucket = self._cd.get_bucket(message)
        return bucket.update_rate_limit()

  @commands.Cog.listener()
  async def on_message(self, message: discord.Message):
    if message.guild is None: return  
    if message.author.bot: return
    res = await self.bot.db.fetchrow("SELECT * FROM levelsetup WHERE guild_id = {}".format(message.guild.id))
    if not res: return 
    che = await self.bot.db.fetchrow("SELECT * FROM levels WHERE guild_id = {} AND author_id = {}".format(message.guild.id, message.author.id))
    retry_after = self.get_ratelimit(message)
    if retry_after: return
    if not che: await self.bot.db.execute("INSERT INTO levels VALUES ($1, $2, $3, $4, $5)", message.guild.id, message.author.id, 2, 0, 2)
    else:
     exp = int(che['exp'])
     total_xp = int(che['total_xp'])
     await self.bot.db.execute("UPDATE levels SET exp = {} WHERE guild_id = {} AND author_id = {}".format(exp+2, message.guild.id, message.author.id))
     await self.bot.db.execute("UPDATE levels SET total_xp = {} WHERE guild_id = {} AND author_id = {}".format(total_xp+2, message.guild.id, message.author.id))
     xp_start = exp+2 
     lvl_start = int(che['level']) 
     xp_end = math.floor(5 * math.sqrt(lvl_start) + 50 * lvl_start + 30) 
     if xp_end < xp_start: 
      if res['destination'] == "channel" or res['destination'] is None:
       if res['channel_id'] is None: await message.channel.send(f"Congratulation {message.author.mention}! You just leveled up to level **{lvl_start + 1}**", allowed_mentions=discord.AllowedMentions(users=True))
       else: 
        channel = message.guild.get_channel(res['channel_id'])
        if channel: await channel.send(f"Congratulation {message.author.mention}! You just leveled up to level **{lvl_start + 1}**", allowed_mentions=discord.AllowedMentions(users=True))
      elif res['destination'] == "dms": 
        try: await message.author.send(f"Congratulation {message.author.mention}! You just leveled up to level **{lvl_start + 1}**", allowed_mentions=discord.AllowedMentions(users=True))
        except: pass  
      await self.bot.db.execute("UPDATE levels SET level = {} WHERE guild_id = {} AND author_id = {}".format(lvl_start + 1, message.guild.id, message.author.id))  
      await self.bot.db.execute("UPDATE levels SET exp = {} WHERE guild_id = {} AND author_id = {}".format(0, message.guild.id, message.author.id))  
      r = await self.bot.db.fetchrow("SELECT role_id FROM levelroles WHERE level = $1 AND guild_id = $2", lvl_start + 1, message.guild.id)
      if r: 
        try: 
          if message.guild.get_role(int(r['role_id'])) is None: return
          if message.guild.get_role(int(r['role_id'])) in message.author.roles: return
          await message.author.add_roles(message.guild.get_role(int(r['role_id'])))
          try: 
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="sent from {}".format(message.guild.name), disabled=True))
            await message.author.send(f"You got a new reward - **@{message.guild.get_role(int(r['role_id'])).name}**", view=view)
          except: pass  
        except: pass
  
  @commands.Cog.listener()
  async def on_member_join(self, member: discord.Member): 
   await asyncio.sleep(2)
   r = await self.bot.db.fetchrow("SELECT level FROM levels WHERE guild_id = $1 AND author_id = $2", member.guild.id, member.id)
   if r: 
    level = int(r['level'])
    results = await self.bot.db.fetch("SELECT role_id FROM levelroles WHERE guild_id = $1 AND level < $2", member.guild.id, level+1)
    if len(results) > 0:
     for result in results: 
      role = member.guild.get_role(int(result['role_id']))
      if role:
       if role.is_assignable(): await member.add_roles(role, reason="giving level roles back to this member")

  @commands.command(description="check any member's rank", help="config", usage="[member]")
  @is_level()
  async def rank(self, ctx, member: discord.Member=Author):
    che = await self.bot.db.fetchrow("SELECT * FROM levels WHERE guild_id = {} AND author_id = {}".format(ctx.guild.id, member.id))
    if not che: return await ctx.reply(embed=discord.Embed(color=self.bot.color, title=f"{member.name}'s rank", description=f"**xp**: `0`\n**level**: `0`").set_author(name=member, icon_url=member.display_avatar.url).set_thumbnail(url=member.display_avatar.url))
    level = int(che['level'])
    xp = int(che['exp'])
    return await ctx.reply(embed=discord.Embed(color=self.bot.color, title=f"{member.name}'s rank", description=f"**xp**: `{str(xp)}`\n**level**: `{level}`").set_author(name=member, icon_url=member.display_avatar.url).set_thumbnail(url=member.display_avatar.url))
  
  @commands.group(invoke_without_command=True)
  async def level(self, ctx): 
     await ctx.create_pages()

  @level.group(invoke_without_command=True, help="config", description="manage the rewards for each level")
  async def rewards(self, ctx: commands.Context): 
    await ctx.create_pages()

  @rewards.command(description="add a level reward", help="config", usage="[level] [role]", brief="manage guild")
  @commands.has_permissions("manage_guild")
  async def add(self, ctx: commands.Context, level: int, *, role: discord.Role): 
    check = await self.bot.db.fetchrow("SELECT level FROM levelroles WHERE guild_id = {} AND level = {}".format(ctx.guild.id, level))
    if check: return await ctx.warn(f"A role has been already assigned for level **{level}**") 
    await self.bot.db.execute("INSERT INTO levelroles VALUES ($1,$2,$3)", ctx.guild.id, level, role.id) 
    await ctx.approve(f"Added {role.mention} for level **{level}** reward")

  @rewards.command(description="remove a level reward", help="config", usage="[level]", brief="manage guild")
  @commands.has_permissions("manage_guild")
  async def remove(self, ctx: commands.Context, level: int=None): 
    check = await self.bot.db.fetchrow("SELECT level FROM levelroles WHERE guild_id = {} AND level = {}".format(ctx.guild.id, level))
    if not check: return await ctx.warn(f"There is no role assigned for level **{level}**")
    await self.bot.db.execute("DELETE FROM levelroles WHERE guild_id = $1 AND level = $2", (ctx.guild.id, level))  
    await ctx.approve(f"Removed level **{level}** reward")
  
  @rewards.command(name="reset", description="reset all level rewards", help="config", brief="server owner")
  @server_owner()
  async def rewards_reset(self, ctx: commands.Context): 
   results = await self.bot.db.fetch("SELECT * FROM levelroles WHERE guild_id = {}".format(ctx.guild.id))
   if len(results) == 0: return await ctx.error("There are no role rewards")
   await self.bot.db.execute("DELETE FROM levelroles WHERE guild_id = $1", ctx.guild.id)
   return await ctx.approve("Reset **all** level rewards") 

  @rewards.command(description="return a list of role rewards", help="config")
  async def list(self, ctx: commands.Context): 
      results = await self.bot.db.fetch("SELECT * FROM levelroles WHERE guild_id = {}".format(ctx.guild.id))
      if len(results) == 0: return await ctx.error("There are no role rewards")
      def sortkey(e): 
        return e[1]
      results.sort(key=sortkey)
      i=0
      k=1
      l=0
      number = []
      messages = []
      num = 0
      auto = ""   
      for table in results:
       level = table['level']
       reward = table['role_id']
       num += 1
       auto += f"\n`{num}` level **{level}** - {ctx.guild.get_role(reward).mention if ctx.guild.get_role(reward) else reward}"
       k+=1
       l+=1
       if l == 10:
         messages.append(auto)
         number.append(discord.Embed(color=self.bot.color, description = auto).set_author(name = f"level rewards", icon_url = ctx.guild.icon.url or None))
         i+=1
         auto = ""
         l=0
      messages.append(auto)
      embed = discord.Embed(description = auto, color = self.bot.color)
      embed.set_author(name = f"level rewards", icon_url = ctx.guild.icon.url or None)
      number.append(embed)
      await ctx.paginate(number)

  @level.command(name="reset", description="reset levels for everyone", help="config", brief="server owner", usage="<member>")
  @server_owner()
  @is_level()
  async def level_reset(self, ctx: commands.Context, *, member: discord.Member=None):
    if not member:
     await self.bot.db.execute("DELETE FROM levels WHERE guild_id = $1", ctx.guild.id)
     return await ctx.approve("Reset levels for **all** members") 
    else: 
     await self.bot.db.execute("DELETE FROM levels WHERE guild_id = $1 AND author_id = $2", ctx.guild.id, member.id)
     return await ctx.approve(f"Reset levels for **{member}**") 

  @level.command(aliases=["lb"], description="check level leaderboard", help="config")
  async def leaderboard(self, ctx: commands.Context):
    await ctx.channel.typing() 
    results = await self.bot.db.fetch("SELECT * FROM levels WHERE guild_id = {}".format(ctx.guild.id))
    if len(results) == 0: return await ctx.error("Nobody is on the **level leaderboard**")
    def sortkey(e): 
      return int(e[4])
    results.sort(key=sortkey, reverse=True)
    i=0
    k=1
    l=0
    messages = []
    num = 0
    auto = ""   
    for table in results:
      user = table['author_id']
      exp = table['exp']
      level = table['level']
      num += 1
      auto += f"\n{'<a:crown:1021829752782323762>' if num == 1 else f'`{num}`'} **{await self.bot.fetch_user(user) or user}** - **{exp}** xp (level {level})"
      k+=1
      l+=1
      if l == 10: break
    messages.append(auto)
    embed = discord.Embed(description = auto, color = self.bot.color)
    embed.set_author(name = f"level leaderboard", icon_url = ctx.guild.icon.url or None)
    await ctx.send(embed=embed)     
         
  @level.command(description="enable leveling system or disable it", help="config", brief="manage guild")
  @commands.has_permissions("manage_guild")
  async def toggle(self, ctx: commands.Context): 
      check = await self.bot.db.fetchrow("SELECT * FROM levelsetup WHERE guild_id = {}".format(ctx.guild.id))        
      if not check:
       await self.bot.db.execute("INSERT INTO levelsetup (guild_id) VALUES ($1)", ctx.guild.id)
       return await ctx.approve("enabled leveling system".capitalize())
      elif check: 
        await self.bot.db.execute("DELETE FROM levelsetup WHERE guild_id = {}".format(ctx.guild.id)) 
        return await ctx.approve("disabled leveling system".capitalize())
  
  @level.command(description="set where the level up message should be sent", help="config", usage="[target]\ntargets: channel, dms, off", brief="manage guild")
  @commands.has_permissions("manage_guild")
  @is_level()
  async def levelup(self, ctx: commands.Context, target: str): 
      if not target in ["dms", "channel", "off"]: return await ctx.warn("Wrong target passed")
      await self.bot.db.execute("UPDATE levelsetup SET destination = $1 WHERE guild_id = $2", target, ctx.guild.id)
      return await ctx.approve(f"Level up message destination: **{target}**")
      
  @level.command(description="set a channel to send level up messages", help="config", usage="[channel]", brief="manage guild")
  @commands.has_permissions("manage_guild")
  @is_level()
  async def channel(self, ctx: commands.Context, *, channel: discord.TextChannel): 
      if not channel: 
       await self.bot.db.execute("UPDATE levelsetup SET channel_id = $1 WHERE guild_id = $2", None, ctx.guild.id)
       return await ctx.approve("removed the channel for leveling system".capitalize())
      elif channel: 
       await self.bot.db.execute("UPDATE levelsetup SET channel_id = $1 WHERE guild_id = $2", channel.id, ctx.guild.id)
       await ctx.approve(f"set the channel for leveling system to {channel.mention}".capitalize())   

async def setup(bot): 
 await bot.add_cog(Leveling(bot))  