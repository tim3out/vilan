import discord
from discord.ext import commands

class Marry(commands.Converter):
  async def convert(self, ctx: commands.Context, argument):
    try: member = await commands.MemberConverter().convert(ctx, argument)
    except commands.BadArgument: member = discord.utils.get(ctx.guild.members, name=argument)
    check = await ctx.bot.db.fetchrow("SELECT * FROM marry WHERE author = $1", member.id)
    che = await ctx.bot.db.fetchrow("SELECT * FROM marry WHERE author = $1", ctx.author.id) 
    if member is None: raise commands.BadArgument(f"No member called **{argument}** found")
    if member == ctx.author: raise commands.BadArgument("You cannot marry yourself")
    if member.bot: raise commands.BadArgument("robots cannot marry")
    if check is not None: raise commands.BadArgument(f"**{member}** is already married")
    else:
      chec = await ctx.bot.db.fetchrow("SELECT * FROM marry WHERE soulmate = $1", member.id)
      if chec is not None: raise commands.BadArgument(f"**{member}** is already married")
    if che is not None: raise commands.BadArgument("You are already **married**")
    else:
      ch = await ctx.bot.db.fetchrow("SELECT * FROM marry WHERE soulmate = $1", ctx.author.id)
      if ch is not None: raise commands.BadArgument("You are already **married**")
    return member

class Message: 
  def good_message(message: discord.Message) -> bool: 
   if not message.guild or message.author.bot or message.content == "": return False 
   return True

class EligibleforEconomy(commands.Converter):
  async def convert(self, ctx: commands.Context, argument):
    try: member = await commands.MemberConverter().convert(ctx, argument)
    except commands.BadArgument: member = discord.utils.get(ctx.guild.members, name=argument)
    check = await ctx.bot.db.fetchrow("SELECT * FROM economy WHERE user_id = $1", member.id)
    if not member: raise commands.BadArgument(f"No member called **{argument}** found")
    if not check: raise commands.BadArgument(f"**{member.name}** doesn't have an economy account")
    if ctx.command.name == 'transfer':
      if member.id == ctx.author.id: raise commands.BadArgument("You cannot transfer with yourself")
    if ctx.command.name == 'rob':
      if check['cash'] == 0: raise commands.BadArgument("This guy is too broke to rob")
      if member.id == ctx.author.id: raise commands.BadArgument("You cannot rob yourself")
    return member

class GoodAmount(commands.Converter):
  async def convert(self, ctx: commands.Context, argument):
    check = await ctx.bot.db.fetchrow("SELECT cash FROM economy WHERE user_id = $1", ctx.author.id)
    check2 = await ctx.bot.db.fetchrow("SELECT bank FROM economy WHERE user_id = $1", ctx.author.id)
    if argument.lower() == "all":
      if ctx.command.name == 'deposit':
        argument = round(check[0], 2)
      if ctx.command.name == 'withdraw':
        argument = round(check2[0], 2)
      if ctx.command.name == 'dice':
        argument = round(check[0], 2)
      if ctx.command.name == 'transfer':
        argument = round(check[0], 2)
    else:
     try:
        argument = int(argument)
     except: raise commands.BadArgument("This is not a number")
    if str(argument)[::-1].find(".") > 2: raise commands.BadArgument("The number can't have more than **2 decimals**")
    if str(argument).startswith("-"): raise commands.BadArgument("This is not a number")
    if ctx.command.name == 'deposit':
      if check[0] == 0: raise commands.BadArgument("You don't have any **money**")
      if check[0] < argument: raise commands.BadArgument("You dont have enough **cash**")
    if ctx.command.name == 'withdraw':
      if check2[0] < argument: raise commands.BadArgument("You dont have that **money**")
      if check2[0] == 0: raise commands.BadArgument("You dont have any **cash**")
    if ctx.command.name == 'dice':
      if argument < 20: raise commands.BadArgument("You cannot bet below 20 💵")
    if ctx.command.name == 'transfer':
      if check[0] < argument: raise commands.BadArgument("You dont have enough **money** to transfer")
      if check[0] == 0: raise commands.BadArgument("You dont have any **cash**")
    if not argument: raise commands.MissingRequiredArgument([argument])
    return argument

class GoodRole(commands.Converter):
  async def convert(self, ctx: commands.Context, argument): 
    try: role = await commands.RoleConverter().convert(ctx, argument)
    except commands.BadArgument: role = discord.utils.get(ctx.guild.roles, name=argument) 
    if role is None: 
      role = ctx.find_role(argument)
      if not role: raise commands.BadArgument(f"No role called **{argument}** found") 
    if role.position >= ctx.guild.me.top_role.position: raise commands.BadArgument("I cannot manage this role") 
    if ctx.author.id == ctx.guild.owner_id: return role 
    if role.position >= ctx.author.top_role.position: raise commands.BadArgument(f"You cannot manage this role")
    return role

class NoStaff(commands.Converter): 
  async def convert(self, ctx: commands.Context, argument): 
    try: member = await commands.MemberConverter().convert(ctx, argument)
    except commands.BadArgument: member = discord.utils.get(ctx.guild.members, name=argument)
    if member is None: raise commands.BadArgument(f"No member called **{argument}** found")  
    if member.id == ctx.guild.me.id: raise commands.BadArgument("why g") 
    if member.top_role.position >= ctx.guild.me.top_role.position: raise commands.BadArgument(f"I cannot execute this command on **{member}**") 
    if ctx.author.id == ctx.guild.owner_id: return member
    if member.top_role.position >= ctx.author.top_role.position or member.id == ctx.guild.owner_id: raise commands.BadArgument(f"You cannot use this command on **{member}**") 
    return member