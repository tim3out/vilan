import discord, random, datetime, humanize, asyncio
from discord.ext import commands
from tools.predicates import create_account, daily_taken, dice_cd, rob_cd, dig_cd
from tools.converters import EligibleforEconomy, GoodAmount
from tools.views import Transfer

class economy(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        self.cash = "💵"
        self.card = "💳"
        self.bank = "🏦"
    
    @commands.command(description="claim the daily credits", help="economy")
    @daily_taken()
    @create_account()
    async def daily(self, ctx: commands.Context):
      check = await self.bot.db.fetchrow("SELECT * FROM economy WHERE user_id = $1", ctx.author.id)
      donor = await self.bot.db.fetchrow("SELECT * FROM donor WHERE user_id = $1", ctx.author.id)
      newcash = round(random.uniform(300, 900), 2)
      if donor:
       newcash += round((40/100)*newcash, 2)
      newclaim = int((datetime.datetime.now() + datetime.timedelta(days=1)).timestamp())
      await self.bot.db.execute("UPDATE economy SET cash = $1, daily = $2 WHERE user_id = $3", round(check['cash']+newcash, 2), newclaim, ctx.author.id)
      return await ctx.neutral(f"You claimed **{round(newcash, 2)}** {self.cash} {'+40%' if donor else ''}\nCome back **tomorrow** to claim again", emoji=self.bank)
    
    @commands.command(aliases=["bal"], description="check a member balance", usage="<member>", help="economy")
    @create_account()
    async def balance(self, ctx: commands.Context, *, member: EligibleforEconomy=commands.Author):
        check = await self.bot.db.fetchrow("SELECT * FROM economy WHERE user_id = $1", member.id)
        embed = discord.Embed(color=self.bot.color, description=f"**{member}'s** balance")
        embed.add_field(name="💵 cash", value=check['cash'])
        embed.add_field(name="🏦 bank", value=check['bank'])
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        if check['daily'] is not None: embed.add_field(name="⏳ daily", value=f"{'**Available**' if int(check['daily']) < datetime.datetime.now().timestamp() else '**{}**'.format(humanize.naturaldate(datetime.datetime.fromtimestamp(check['daily'])))}")
        return await ctx.reply(embed=embed)
    
    @commands.command(description="deposit money into the bank", usage="[amount]", aliases=["dep"], help="economy")
    @create_account()
    async def deposit(self, ctx: commands.Context, *, amount: GoodAmount):
      check = await self.bot.db.fetchrow("SELECT * FROM economy WHERE user_id = $1", ctx.author.id)
      await self.bot.db.execute("UPDATE economy SET cash = $1, bank = $2 WHERE user_id = $3", round(check['cash']-amount, 2), round(check['bank']+amount, 2), ctx.author.id)
      return await ctx.neutral(f"Deposited **{amount}** {self.cash} in your bank", emoji=self.bank)
    
    @commands.command(escription="withdraw money from the bank", usage="[amount]", help="economy")
    @create_account()
    async def withdraw(self, ctx: commands.Context, *, amount: GoodAmount):
      check = await self.bot.db.fetchrow("SELECT * FROM economy WHERE user_id = $1", ctx.author.id)
      await self.bot.db.execute("UPDATE economy SET cash = $1, bank = $2 WHERE user_id = $3", round(check['cash']+amount, 2), round(check['bank']-amount, 2), ctx.author.id)
      return await ctx.neutral(f"Withdrawed **{amount}** {self.cash} from your bank", emoji=self.bank)
    
    @commands.command(description="dice your money", usage="[amount]", help="economy")
    @dice_cd()
    @create_account()
    async def dice(self, ctx: commands.Context, *, amount: GoodAmount):
      check = await self.bot.db.fetchrow("SELECT * FROM economy WHERE user_id = $1", ctx.author.id)
      my_dice = random.randint(1, 6) + random.randint(1, 6)
      bot_dice = random.randint(1, 6) + random.randint(1, 6)
      if my_dice > bot_dice:
        await ctx.send(f"You won **{amount}** {self.cash}")
        await self.bot.db.execute("UPDATE economy SET cash = $1, dice = $2 WHERE user_id = $3", round(check['cash']+amount, 2), int((datetime.datetime.now() + datetime.timedelta(seconds=25)).timestamp()), ctx.author.id)
      elif bot_dice > my_dice:
        await ctx.send(f"You lost **{amount}** {self.cash}")
        await self.bot.db.execute("UPDATE economy SET cash = $1, dice = $2 WHERE user_id = $3", round(check['cash']-amount, 2), int((datetime.datetime.now() + datetime.timedelta(seconds=25)).timestamp()), ctx.author.id)
      else:
        await ctx.send("It's a tie!")
        await self.bot.db.execute("UPDATE economy SET dice = $1 WHERE user_id = $2", int((datetime.datetime.now() + datetime.timedelta(seconds=25)).timestamp()), ctx.author.id)
    
    @commands.command(description="transfer cash to a member", usage="[amount] [member]", help="economy")
    @create_account()
    async def transfer(self, ctx: commands.Context, amount: GoodAmount, *, member: EligibleforEconomy):
      embed = discord.Embed(color=self.bot.color, description=f"{ctx.author.mention}: Are you sure you want to transfer **{amount}** {self.cash} to **{member.mention}**")
      view = Transfer(ctx, member, amount)
      view.message = await ctx.send(embed=embed, view=view)
    
    @commands.command(description="rob someone's money", usage="[member]", help="economy")
    @rob_cd()
    @create_account()
    async def rob(self, ctx: commands.Context, member: EligibleforEconomy):
      check = await self.bot.db.fetchrow("SELECT * FROM economy WHERE user_id = $1", member.id)
      check2 = await self.bot.db.fetchrow("SELECT cash FROM economy WHERE user_id = $1", ctx.author.id)
      if check["cash"] <= 100: amount = round(random.randrange(0, check["cash"]/2))
      else: amount = round(random.randrange(200, 600), 2)
      await self.bot.db.execute("UPDATE economy SET cash = $1 WHERE user_id = $2", round(check['cash']-amount, 2), member.id)
      await self.bot.db.execute("UPDATE economy SET cash = $1, rob = $2 WHERE user_id = $3", round(check2[0]+amount, 2), int((datetime.datetime.now() + datetime.timedelta(days=1)).timestamp()), ctx.author.id)
      await ctx.neutral(f"Robbed **{amount}** {self.cash} from **{member}**", emoji=self.bank)
      await member.send(f"Oh noo! **{ctx.author.name}** robbed **{amount}** {self.cash} from you. To prevent this happening in the future, store your cash in the bank")
    
    @commands.command(description="dig for a chance to find rare ores", help="economy")
    @dig_cd()
    @create_account()
    async def dig(self, ctx: commands.Context):
      check = await self.bot.db.fetchrow("SELECT * FROM economy WHERE user_id = $1", ctx.author.id)
      ores = ["iron", "iron", "iron", "iron", "iron", "iron", "gold", "gold", "gold", "coper", "coper", "coper", "coper", "coal", "coal", "coal", "coal", "coal", "coal", "coal", "coal", "amethist", "diamond"]
      ore = random.choice(ores)
      if ore == "iron": 
        amount = round(random.uniform(70, 120), 2)
      if ore == "gold": 
        amount = round(random.uniform(140, 340), 2)
      if ore == "diamond": 
        amount = round(random.uniform(600, 100), 2)
      if ore == "coper": 
        amount = round(random.uniform(30, 80), 2)
      if ore == "amethist": 
        amount = round(random.uniform(1500, 2500), 2)
      if ore == "coal": 
        amount = round(random.uniform(5, 40), 2)
      message = await ctx.neutral(f"Started digging for ores....")
      await asyncio.sleep(2)
      nextdig = int((datetime.datetime.now() + datetime.timedelta(minutes=3)).timestamp())
      await self.bot.db.execute("UPDATE economy SET cash = $1, dig = $2 WHERE user_id = $3", round(check['cash']+amount, 2), nextdig, ctx.author.id)
      return await message.edit(embed=discord.Embed(color=self.bot.color, description=f"<:ore:1146484142213697637> {ctx.author.mention}: You just found a **{ore}** ore, that is worth **{amount}** {self.cash}"))
    
    @commands.command(description="global leaderboard for economy", help="economy", aliases=["lb"])
    async def leaderboard(self, ctx: commands.Context): 
     results = await self.bot.db.fetch("SELECT * FROM economy")
     if len(results) == 0: return await ctx.warn("yall broke")
     def key(results):
      results[1]+results[2]
     i=0
     k=1
     l=0
     mes = ""
     number = []
     messages = []
     results.sort(reverse=True, key= lambda c: c['cash']+c['bank'])
     for res in results:
      mes = f"{mes}`{k}` **{self.bot.get_user(res[0])}** - {res[1]+res[2]:,} {self.cash}\n"
      k+=1
      l+=1
      if l == 10:
       messages.append(mes)
        
       number.append(discord.Embed(color=self.bot.color, title=f"economy leaderboard ({len(results)})", description=messages[i]).set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url))
       i+=1
       mes = ""
       l=0
    
     messages.append(mes)

     number.append(discord.Embed(color=self.bot.color, title=f"economy leaderboard ({len(results)})", description=messages[i]).set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url))
     await ctx.paginate(number)
    
async def setup(bot):
    await bot.add_cog(economy(bot))