import discord
from discord.ext import commands
from tools.predicates import premium, is_reskin
from tools.converters import NoStaff

class donor(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
    
    @commands.command(description="purge an amount of messages sent by you", usage="[amount]", help="donor")
    @premium()
    async def selfpurge(self, ctx: commands.Context, amount: int):
     if not amount: await ctx.channel.delete_messages([message async for message in ctx.channel.history() if message.author == ctx.author])
     else:
      mes = []
      async for message in ctx.channel.history():
       if (len(mes) == amount +1): break
       if message.author == ctx.author: mes.append(message) 
      await ctx.channel.delete_messages(mes)
    
    @commands.group(invoke_without_command=True)
    async def reskin(self, ctx: commands.Context):
        await ctx.create_pages()
    
    @reskin.command(name="enable", description="enable reskin module in the server", help="donor", aliases=["e"], brief="manage server")
    @commands.has_permissions("manage_guild")
    async def reskin_enable(self, ctx: commands.Context):
      check = await self.bot.db.fetchrow("SELECT * FROM reskin_toggle WHERE guild_id = $1", ctx.guild.id)
      if check: return await ctx.error("Reskin is **already** enabled")
      await self.bot.db.execute("INSERT INTO reskin_toggle VALUES ($1)", ctx.guild.id)
      return await ctx.approve("Reskin has been **enabled**")
    
    @reskin.command(name="disable", description="disable reskin module in the server", help="donor", aliases=["d"], brief="manage server")
    @commands.has_permissions("manage_guild")
    async def reskin_disable(self, ctx: commands.Context):
      check = await self.bot.db.fetchrow("SELECT * FROM reskin_toggle WHERE guild_id = $1", ctx.guild.id)
      if not check: return await ctx.error("Reskin is **not** enabled")
      await self.bot.db.execute("DELETE FROM reskin_toggle WHERE guild_id = $1", ctx.guild.id)
      return await ctx.approve("Reskin has been **disabled**")
    
    @reskin.command(description="edit your reskin name", name="name", usage="[name]", help="donor", brief="donor")
    @is_reskin()
    @premium()
    async def reskin_name(self, ctx: commands.Context, *, name: str):
      check = await self.bot.db.fetchrow("SELECT * FROM reskin WHERE user_id = $1", ctx.author.id)
      if not check: await self.bot.db.execute("INSERT INTO reskin VALUES ($1,$2,$3)", ctx.author.id, name, self.bot.user.avatar.url)
      await self.bot.db.execute("UPDATE reskin SET name = $1 WHERE user_id = $2", name, ctx.author.id)
      return await ctx.approve(f"Reskin name set to **{name}**")
    
    @reskin.command(description="edit your reskin avatar", name="avatar", usage="[url]", aliases=["av"], help="donor", brief="donor")
    @is_reskin()
    @premium()
    async def reskin_avatar(self, ctx: commands.Context, *, url: str):
      if not url: return await ctx.error("This is not an image")
      await self.bot.db.execute("UPDATE reskin SET avatar = $1 WHERE user_id = $2", url, ctx.author.id)
      return await ctx.approve("Set your reskin avatar")
    
    @reskin.command(description="delete your reskin", name="delete", help="donor", brief="donor")
    @is_reskin()
    @premium()
    async def reskin_delete(self, ctx: commands.Context):
      check = await self.bot.db.fetchrow("SELECT * FROM reskin WHERE user_id = $1", ctx.author.id)
      if not check: return await ctx.warn("You don't have a reskin set")
      await self.bot.db.execute("DELETE FROM reskin WHERE user_id = $1", ctx.author.id)
      return await ctx.approve("Your reskin has been deleted")
    
    @commands.command(description="uwuify a person's messages", usage="[member]", brief="manage messages & donor", help="donor")
    @commands.has_permissions("manage_messages")
    @premium()
    async def uwulock(self, ctx: commands.Context, *, member: NoStaff): 
      if member.bot: return await ctx.warn("You cannot **uwulock** a bot")
      check = await self.bot.db.fetchrow("SELECT user_id FROM uwulock WHERE user_id = {} AND guild_id = {}".format(member.id, ctx.guild.id))    
      if not check: await self.bot.db.execute("INSERT INTO uwulock VALUES ($1,$2)", ctx.guild.id, member.id)
      else: await self.bot.db.execute("DELETE FROM uwulock WHERE user_id = {} AND guild_id = {}".format(member.id, ctx.guild.id))    
      return await ctx.message.add_reaction("<:catthumbsup:1133831377440219298>")
    
    @commands.command(description="check the premium perks", help="info")
    async def perks(self, ctx: commands.Context): 
      embed = discord.Embed(color=self.bot.color, title="donator perks", description="Boost the [**support server**](https://discord.gg/DX4MxrxsCg) to get access to these perks.")
      embed.add_field(name="perks", value=f"**reskin name** - edit your rchecn name\n**reskin avatar** - edit your reskin avatat\n**selfpurge** - delete your own messages\n**uwulock** - uwuify a person messages\n**forcenick** - lock a nickname to a member\n**lastfm mode steal** - steal a user lastfm mode\n**lastfm mode set** - set a lastfm embed\n**lastfm mode remove** - remove your lastfm embed\n**lastfm mode view** - view your lastfm embed\n\n**+40%** more daily credits", inline=False) 
      return await ctx.reply(embed=embed) 
    
    @commands.command(aliases=["cr"])
    @premium()
    async def colorrole(self, ctx: commands.Context, *, color):
      role = await ctx.guild.create_role(name=f"{ctx.author.name}'s color", color=str(discord.Color(color)))
      await role.edit(ctx.author.top_role.position)
      await self.bot.db.execute("INSERT INTO colorrole VALUES ($1,$2)", ctx.author.id, role.id)
      return await ctx.approve("Created your color role")
    
    @commands.command(description="lock a nicknames to an user", help="donor", usage="[member] [nickname]\nif none is passed as nickname, the force nickname gets removed", aliases=["locknick"], brief="manage nicknames & donor")
    @commands.has_permissions("manage_nicknames")
    @premium()
    async def forcenick(self, ctx: commands.Context, member: NoStaff, *, nick: str): 
      if nick.lower() == "none": 
        check = await self.bot.db.fetchrow("SELECT * FROM forcenick WHERE user_id = {} AND guild_id = {}".format(member.id, ctx.guild.id))
        if not check: return await ctx.warn(f"**No** forcenick found for {member}")
        await self.bot.db.execute("DELETE FROM forcenick WHERE user_id = {} AND guild_id = {}".format(member.id, ctx.guild.id))              
        await member.edit(nick=None)
        await ctx.message.add_reaction("<:catthumbsup:974982144021626890>")
      else: 
        check = await self.bot.db.fetchrow("SELECT * FROM forcenick WHERE user_id = {} AND guild_id = {}".format(member.id, ctx.guild.id))   
        if not check: await self.bot.db.execute("INSERT INTO forcenick VALUES ($1,$2,$3)", ctx.guild.id, member.id, nick)
        else: await self.bot.db.execute("UPDATE forcenick SET nickname = '{}' WHERE user_id = {} AND guild_id = {}".format(nick, member.id, ctx.guild.id))  
        await member.edit(nick=nick)
        await ctx.message.add_reaction("<:catthumbsup:974982144021626890>")  
    
async def setup(bot):
    await bot.add_cog(donor(bot))