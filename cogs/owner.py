import discord, datetime
from discord.ext import commands

class owner(commands.Cog):
  def __init__(self, bot: commands.AutoShardedBot):
    self.bot = bot
  
  @commands.group(invoke_without_command=True)
  @commands.is_owner()
  async def donor(self, ctx):
    await ctx.create_pages()
  
  @donor.command()
  @commands.is_owner()
  async def add(self, ctx, *, member: discord.User):
    check = await self.bot.db.fetchrow("SELECT * FROM donor WHERE user_id = $1", member.id)
    if check: return await ctx.warn(f"**{member}** is already a donor")
    await self.bot.db.execute("INSERT INTO donor VALUES ($1,$2)", member.id, int(datetime.datetime.now().timestamp()))
    return await ctx.approve(f"**{member}** is now a donor")
  
  @donor.command()
  @commands.is_owner()
  async def remove(self, ctx, *, member: discord.User):
    check = await self.bot.db.fetchrow("SELECT * FROM donor WHERE user_id = $1", member.id)
    if not check: return await ctx.warn(f"**{member}** is not a donor")
    await self.bot.db.execute("DELETE FROM donor WHERE user_id = $1", member.id)
    return await ctx.approve(f"**{member}** is not a donor anymore")
  
  @commands.command()
  @commands.is_owner()
  async def portal(self, ctx, id: int):
    await ctx.message.delete()      
    guild = self.bot.get_guild(id)
    for c in guild.text_channels:
      if c.permissions_for(guild.me).create_instant_invite: 
        invite = await c.create_invite()
        await ctx.author.send(f"{guild.name} invite link - {invite}")
        break
  
  @commands.command(aliases=["servers"])
  @commands.is_owner()
  async def guilds(self, ctx: commands.Context):
    def key(s):
        return s.member_count
    i=0
    k=1
    l=0
    mes = ""
    number = []
    messages = []
    lis = [g for g in self.bot.guilds]
    lis.sort(reverse=True, key=key)
    for guild in lis:
        mes = f"{mes}`{k}` {guild.name} ({guild.id}) - ({guild.member_count})\n"
        k+=1
        l+=1
        if l == 10:
            messages.append(mes)
            number.append(discord.Embed(color=self.bot.color, title=f"guilds ({len(self.bot.guilds)})", description=messages[i]))
            i+=1
            mes = ""
            l=0
             
    messages.append(mes)
    number.append(discord.Embed(color=self.bot.color, title=f"guilds ({len(self.bot.guilds)})", description=messages[i]))
    await ctx.paginate(number)
  
  @commands.command(aliases=["trace"])
  @commands.is_owner()
  async def geterror(self, ctx: commands.Context, *, key: str):
    check = await self.bot.db.fetchrow("SELECT * FROM cmderror WHERE code = $1", key)
    if not check: return await ctx.warn(f"No error with code `{key}`")
    return await ctx.reply(embed=discord.Embed(color=self.bot.color, title=f"error for {key}", description=f"```{check['error']}```"))
  
  @commands.command()
  @commands.is_owner()
  async def delerrors(self, ctx):
    await self.bot.db.execute("DELETE FROM cmderror")
    return await ctx.reply("deleted all errors")
  
  @commands.command()
  @commands.is_owner()
  async def r(self, ctx):
    await ctx.bot.close()
  
  @commands.group(invoke_without_command=True)
  @commands.is_owner()
  async def blacklist(self, ctx):
    return await ctx.create_pages()
  
  @blacklist.command(help="owner", description="blacklist a user", usage="[user]", brief="bot owner")
  @commands.is_owner()
  async def user(self, ctx, *, member: discord.User):
    if member.id in self.bot.owner_ids: return await ctx.error("You cant blacklist a bot owner")
    check = await self.bot.db.fetchrow("SELECT * FROM nodata WHERE user_id = $1", member.id)
    if check: 
      await self.bot.db.execute("DELETE FROM nodata WHERE user_id = $1", member.id)
      return await ctx.approve(f"{member.mention} is no longer blacklisted")
    await self.bot.db.execute("INSERT INTO nodata (user_id, state) VALUES ($1,$2)", member.id, "false")
    return await ctx.approve(f"{member.mention} is now blacklisted")
  
  @blacklist.command(description="blacklist a guild", help="owner", usage="[guild id]", brief="bot owner")
  @commands.is_owner()
  async def guild(self, ctx, *, guildid: int):
    if guildid in self.bot.main_guilds: return await ctx.error("You cant blacklist this guild")
    check = await self.bot.db.fetchrow("SELECT * FROM nodata WHERE guild_id = $1", guildid)
    if check: 
      await self.bot.db.execute("DELETE FROM nodata WHERE guild_id = $1", guildid)
      return await ctx.approve(f"{guildid} is no longer blacklisted")
    await self.bot.db.execute("INSERT INTO nodata (guild_id, state) VALUES ($1,$2)", guildid, "false")
    return await ctx.approve(f"{guildid} is now blacklisted")
  
async def setup(bot):
    await bot.add_cog(owner(bot))