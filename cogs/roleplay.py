import discord, asyncio, random
from discord.ext import commands
from tools.predicates import check_pot, pot_owner
from tools.views import MarryView, DivorceView
from tools.converters import Marry

class roleplay(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.pot_emoji = "🍃"
        self.pot_color = 0x57D657
        self.smoke = "🌬"
        self.bot = bot
    
    async def pot_send(self, ctx: commands.Context, message: str) -> discord.Message:
      return await ctx.reply(embed=discord.Embed(color=self.pot_color, description=f"{self.pot_emoji} {ctx.author.mention}: {message}"))

    async def smoke_send(self, ctx: commands.Context, message: str) -> discord.Message:
      return await ctx.reply(embed=discord.Embed(color=self.bot.color, description=f"{self.smoke} {ctx.author.mention}: {message}"))
    
    @commands.group(name="pot", invoke_without_command=True)
    async def potcmd(self, ctx):
      await ctx.create_pages()
    
    @potcmd.command(name="toggle", description="toggle the server pot", brief="manage guild", help="roleplay")
    @commands.has_permissions("manage_guild")
    async def pot_toggle(self, ctx: commands.Context):
     check = await self.bot.db.fetchrow("SELECT * FROM pot WHERE guild_id = {}".format(ctx.guild.id))
     if not check:
      await self.bot.db.execute("INSERT INTO pot VALUES ($1,$2,$3)", ctx.guild.id, 0, ctx.author.id)
      return await self.pot_send(ctx, "The pot is **yours**")
     await self.bot.db.execute("DELETE FROM pot WHERE guild_id = $1", ctx.guild.id)
     return await self.smoke_send(ctx, "Lost the server's pot")
    
    @potcmd.command(name="stats", description="check pot stats", aliases=["status", "settings"], help="roleplay")
    @check_pot()
    async def pot_stats(self, ctx: commands.Context):
      check = await self.bot.db.fetchrow("SELECT * FROM pot WHERE guild_id = $1", ctx.guild.id)
      embed = discord.Embed(color=self.pot_color, description=f"{self.smoke} hits: **{check['hits']}**\n{self.pot_emoji} holder: <@{check['holder']}>")
      embed.set_author(icon_url=ctx.guild.icon, name=f"{ctx.guild.name}'s pot")
      return await ctx.reply(embed=embed)

    @potcmd.command(name="hit", description="hit the server pot", help="roleplay")
    @check_pot()
    @pot_owner()
    async def pot_hit(self, ctx: commands.Context):
      mes = await self.pot_send(ctx, "Hitting the **pot**....")
      await asyncio.sleep(2)
      check = await self.bot.db.fetchrow("SELECT * FROM pot WHERE guild_id = $1", ctx.guild.id)
      newhits = int(check["hits"]+1)
      embed = discord.Embed(color=self.bot.color, description=f"{self.smoke} {ctx.author.mention}: You just hit the **pot**. This server has now a total of **{newhits}** hits!")
      await mes.edit(embed=embed)
      await self.bot.db.execute("UPDATE pot SET hits = $1 WHERE guild_id = $2", newhits, ctx.guild.id)
    
    @pot_hit.error 
    async def on_error(self, ctx: commands.Context, error: Exception): 
     if isinstance(error, commands.CommandOnCooldown): return await self.pot_send(ctx, "Slow down g, You are getting too high")
    
    @potcmd.command(name="pass", description="pass the pot to someone else", usage="[member]", help="roleplay")
    @check_pot()
    @pot_owner()
    async def pot_pass(self, ctx: commands.Context, *, member: discord.Member):
     if member.id == self.bot.user.id: return await ctx.reply("I don't smoke thanks")
     elif member.bot: return await ctx.warn("Bots don't smoke")
     elif member.id == ctx.author.id: return await ctx.warn("You already have the **pot**")
     await self.bot.db.execute("UPDATE pot SET holder = $1 WHERE guild_id = $2", member.id, ctx.guild.id)
     await self.pot_send(ctx, f"**Pot** passed to **{member.name}**")
    
    @potcmd.command(name="steal", description="steal the server's pot", help="roleplay")
    @check_pot()
    async def pot_steal(self, ctx: commands.Context):
     check = await self.bot.db.fetchrow("SELECT * FROM pot WHERE guild_id = $1", ctx.guild.id)
     if check["holder"] == ctx.author.id: return await self.pot_send(ctx, "You already have the **pot**")
     chances = ["yes", "yes", "yes", "no", "no"]
     if random.choice(chances) == "no": return await self.smoke_send(ctx, f"You tried to steal the **pot** and **{(await self.bot.fetch_user(int(check['holder']))).name}** hit you")
     await self.bot.db.execute("UPDATE pot SET holder = $1 WHERE guild_id = $2", ctx.author.id, ctx.guild.id)
     return await self.pot_send(ctx, "You got the server **pot**")
    
    @commands.command(description="kiss an user", usage="[member]", help="roleplay")
    async def kiss(self, ctx: commands.Context, *, member: discord.Member):
     lol = await self.bot.session.json("http://api.nekos.fun:8080/api/kiss")
     embed = discord.Embed(color=self.bot.color, description=f"*Aww how cute!* **{ctx.author.name}** kissed **{member.name}**")
     embed.set_image(url=lol["image"])
     return await ctx.reply(embed=embed)

    @commands.command(description="cuddle an user", usage="[member]", help="roleplay")
    async def cuddle(self, ctx, *, member: discord.Member):
     lol = await self.bot.session.json("http://api.nekos.fun:8080/api/cuddle")
     embed = discord.Embed(color=self.bot.color, description=f"*Aww how cute!* **{ctx.author.name}** cuddled **{member.name}**")
     embed.set_image(url=lol["image"])
     return await ctx.reply(embed=embed)

    @commands.command(description="hug an user", usage="[member]", help="roleplay")
    async def hug(self, ctx: commands.Context, *, member: discord.Member): 
     lol = await self.bot.session.json(f"http://api.nekos.fun:8080/api/{ctx.command.name}")
     embed = discord.Embed(color=self.bot.color, description=f"*Aww how cute!* **{ctx.author.name}** hugged **{member.name}**")
     embed.set_image(url=lol["image"])
     return await ctx.reply(embed=embed)

    @commands.command(description="pat an user", usage="[member]", help="roleplay")
    async def pat(self, ctx, *, member: discord.Member):
     lol = await self.bot.session.json(f"http://api.nekos.fun:8080/api/{ctx.command.name}")
     embed = discord.Embed(color=self.bot.color, description=f"*Aww how cute!* **{ctx.author.name}** pats **{member.name}**")
     embed.set_image(url=lol["image"])
     return await ctx.reply(embed=embed)

    @commands.command(description="slap an user", usage="[member]", help="roleplay")
    async def slap(self, ctx, *, member: discord.Member): 
     lol = await self.bot.session.json(f"http://api.nekos.fun:8080/api/{ctx.command.name}")
     embed = discord.Embed(color=self.bot.color, description=f"**{ctx.author.name}** slaps **{member.name}***")
     embed.set_image(url=lol["image"])
     return await ctx.reply(embed=embed)

    @commands.command(description="start laughing", help="roleplay")
    async def laugh(self, ctx): 
     lol = await self.bot.session.json(f"http://api.nekos.fun:8080/api/{ctx.command.name}")
     embed = discord.Embed(color=self.bot.color, description=f"**{ctx.author.name}** laughs")
     embed.set_image(url=lol["image"])
     return await ctx.reply(embed=embed)

    @commands.command(description="start crying", help="roleplay")
    async def cry(self, ctx):
     lol = await self.bot.session.json(f"http://api.nekos.fun:8080/api/{ctx.command.name}")
     embed = discord.Embed(color=self.bot.color, description=f"**{ctx.author.name}** cries")
     embed.set_image(url=lol["image"])
     return await ctx.reply(embed=embed)
    
    @commands.command(description="marry an user", help="roleplay", usage="[user]")
    async def marry(self, ctx: commands.Context, *, member: Marry):
      embed = discord.Embed(color=self.bot.color, description=f"**{ctx.author.name}** wants to marry you. do you accept?")
      view = MarryView(ctx, member)
      view.message = await ctx.reply(content=member.mention, embed=embed, view=view)
    
    @commands.command(description="check an user's marriage", usage="<member>", help="roleplay")
    async def marriage(self, ctx: commands.Context, *, member: discord.User=commands.Author):
      check = await self.bot.db.fetchrow("SELECT * FROM marry WHERE author = $1", member.id)       
      if check is None:
           check2 = await self.bot.db.fetchrow("SELECT * FROM marry WHERE soulmate = $1", member.id)
           if check2 is None: return await ctx.error(f"{'**You** are' if member == ctx.author else f'**{member.name}** is'} not **married**")
           elif check2 is not None:
            embed = discord.Embed(color=self.bot.color, description=f"💒 {f'**{member}** is' if member != ctx.author else '**You** are'} currently married to **{await self.bot.fetch_user(int(check2[0]))}**")
            return await ctx.reply(embed=embed)  
      elif check is not None:
         embed = discord.Embed(color=self.bot.color, description=f"💒 {f'**{member}** is' if member != ctx.author else '**You** are'} currently married to **{await self.bot.fetch_user(int(check[1]))}**")
         return await ctx.reply(embed=embed)   

    @commands.command(description="divorce from your partner", help="roleplay")
    async def divorce(self, ctx: commands.Context):
      check = await self.bot.db.fetchrow("SELECT * FROM marry WHERE author = $1", ctx.author.id)
      if not check:
        check2 = await self.bot.db.fetchrow("SELECT * FROM marry WHERE soulmate = $1", ctx.author.id)
      if not check2: return await ctx.error("You are **not** married")
      view = DivorceView(ctx)
      view.message = await ctx.reply(embed=discord.Embed(color=self.bot.color, description=f"**{ctx.author.name}** are you sure you want to divorce with your partner?"), view=view)
    
async def setup(bot):
    await bot.add_cog(roleplay(bot))