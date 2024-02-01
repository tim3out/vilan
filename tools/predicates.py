import discord, datetime, humanize
from discord.ext import commands
from .helpers import has_perms

def create_account():
 async def predicate(ctx: commands.Context):
   check = await ctx.bot.db.fetchrow("SELECT * FROM economy WHERE user_id = $1", ctx.author.id)
   ts = datetime.datetime.now().timestamp()
   if not check:
    await ctx.bot.db.execute("INSERT INTO economy VALUES ($1,$2,$3,$4,$5,$6,$7)", ctx.author.id, 0, 0, ts, ts, ts, ts)
   return True
 return commands.check(predicate)

def daily_taken():
  async def predicate(ctx: commands.Context):
    check = await ctx.bot.db.fetchrow("SELECT daily FROM economy WHERE user_id = $1", ctx.author.id)
    if check[0] > int(datetime.datetime.now().timestamp()):
      date = datetime.datetime.fromtimestamp(check[0])
      await ctx.warn(f"You **already** have claimed your daily credits\nTry again **{humanize.naturaltime(date)}**")
      return False
    return True
  return commands.check(predicate)

def dice_cd():
  async def predicate(ctx: commands.Context):
    check = await ctx.bot.db.fetchrow("SELECT dice FROM economy WHERE user_id = $1", ctx.author.id)
    if check[0] > int(datetime.datetime.now().timestamp()):
      date = datetime.datetime.fromtimestamp(check[0])
      await ctx.warn(f"Please wait **{humanize.naturaltime(date)}** before using dice again")
      return False
    return True
  return commands.check(predicate)

def rob_cd():
  async def predicate(ctx: commands.Context):
    check = await ctx.bot.db.fetchrow("SELECT rob FROM economy WHERE user_id = $1", ctx.author.id)
    if check[0] > int(datetime.datetime.now().timestamp()):
      date = datetime.datetime.fromtimestamp(check[0])
      await ctx.warn(f"You can rob again **{humanize.naturaltime(date)}**")
      return False
    return True
  return commands.check(predicate)

def dig_cd():
  async def predicate(ctx: commands.Context):
    check = await ctx.bot.db.fetchrow("SELECT dig FROM economy WHERE user_id = $1", ctx.author.id)
    if check[0] > int(datetime.datetime.now().timestamp()):
      date = datetime.datetime.fromtimestamp(check[0])
      await ctx.warn(f"Please wait **{humanize.naturaltime(date)}** before digging again")
      return False
    return True
  return commands.check(predicate)

def check_pot():
 async def predicate(ctx: commands.Context):
  check = await ctx.bot.db.fetchrow("SELECT * FROM pot WHERE guild_id = $1", ctx.guild.id)
  if not check: await ctx.warn(f"This server doesn't have a **pot** active. Use `{ctx.clean_prefix}pot toggle` to get one")   
  return check is not None
 return commands.check(predicate)
  
def pot_owner(): 
 async def predicate(ctx: commands.Context): 
  check = await ctx.bot.db.fetchrow("SELECT * FROM pot WHERE guild_id = $1", ctx.guild.id)
  if check["holder"] != ctx.author.id: await ctx.warn(f"You don't have the server **pot**. Steal it from <@{check['holder']}>")
  return check["holder"] == ctx.author.id
 return commands.check(predicate) 

def premium():
  async def predicate(ctx: commands.Context):
    check = await ctx.bot.db.fetchrow("SELECT * FROM donor WHERE user_id = $1", ctx.author.id)
    if not check:
      await ctx.warn("You are not a donor")
      return False
    return True
  return commands.check(predicate)

async def check_vc_owner(ctx: commands.Context):
  if not ctx.author.voice:
    await ctx.bot.ext.warn(ctx, "You are not in a voice channel")
    check = await ctx.bot.db.fetchrow("SELECT * FROM vcs WHERE voice = $1 AND user_id = $2", ctx.author.voice.channel.id, ctx.author.id)
    if not check: 
        await ctx.bot.ext.warn(ctx, "You are not the owner of this voice channel")
        return True                

async def check_voice(ctx: commands.Context):
  check = await ctx.bot.db.fetchrow("SELECT * FROM voicemaster WHERE guild_id = $1", ctx.guild.id) 
  if check:     
    channeid = check[1]
    voicechannel = ctx.guild.get_channel(channeid)
    category = voicechannel.category 
    if not ctx.author.voice:
      await ctx.bot.ext.warn(ctx, "You are not in a voice channel")
      return True
    elif ctx.author.voice:
      if ctx.author.voice.channel.category != category:
        await ctx.bot.ext.warn(ctx, "You are not in a voice channel created by the bot")
        return True

async def check_vc(interaction: discord.Interaction, category: discord.CategoryChannel): 
  if not interaction.user.voice:
    await interaction.warn("You are not in a voice channel")
    return False
  elif interaction.user.voice:
      if interaction.user.voice.channel.category != category:
         await interaction.warn("You are not in a voice channel created by the bot")
         return False
      return True   

def check_owner(): 
   async def predicate(ctx: commands.Context): 
     voice = await check_voice(ctx)
     owner = await check_owner(ctx)
     if voice is True or owner is True: return False 
     return True 
   return commands.check(predicate)

def has_booster_role(): 
 async def predicate(ctx: commands.Context): 
  che = await ctx.bot.db.fetchrow("SELECT * FROM booster_module WHERE guild_id = {}".format(ctx.guild.id))
  if not che:
    await ctx.warn("Booster role module is **not** configured")
    return False
  check = await ctx.bot.db.fetchrow("SELECT * FROM booster_roles WHERE guild_id = {} AND user_id = {}".format(ctx.guild.id, ctx.author.id))
  if not check:  
   await ctx.warn("You do not have a booster role\nCreate one using ```;br create```")
   return False 
  return True 
 return commands.check(predicate)

def server_owner(): 
 async def predicate(ctx: commands.Context): 
  if ctx.author.id != ctx.guild.owner_id:
    await ctx.warn(f"This command can be used only by **{ctx.guild.owner.name}**")
    return False
  return True
 return commands.check(predicate)

def is_antinuke():
 async def predicate(ctx: commands.Context): 
  check = await ctx.bot.db.fetchrow("SELECT * FROM antinuke_toggle WHERE guild_id = $1", ctx.guild.id)
  if not check: await ctx.warn("Antinuke is **not** enabled")
  return check is not None 
 return commands.check(predicate)     

def can_manage(): 
 async def predicate(ctx: commands.Context): 
  if ctx.author.id != ctx.guild.owner.id:
    await ctx.warn(f"This command can only be used by **{ctx.guild.owner.name}**\nIf the account cannot be accessed, please join the [**support server**](https://discord.gg/DX4MxrxsCg)")
    return False
  return True 
 return commands.check(predicate)

def check_whitelist(module: str):
   async def predicate(ctx: commands.Context):
    if ctx.guild is None: return False 
    if ctx.author.id == ctx.guild.owner.id: return True
    check = await ctx.bot.db.fetchrow("SELECT * FROM whitelist WHERE guild_id = $1 AND object_id = $2 AND mode = $3 AND module = $4", ctx.guild.id, ctx.author.id, "user", module)   
    if check is None: 
     await ctx.warn(f"You are not **whitelisted** for **{module}**") 
     return False      
    return True
   return commands.check(predicate) 

def is_mod(): 
  async def predicate(ctx: commands.Context): 
   check = await ctx.bot.db.fetchrow("SELECT * FROM mod WHERE guild_id = $1", ctx.guild.id)
   if not check: 
    await ctx.warn(f"Moderation isn't **enabled**. Enable it using `{ctx.clean_prefix}setmod` command")
    return False
   return True
  return commands.check(predicate)

def is_level(): 
  async def predicate(ctx: commands.Context): 
   check = await ctx.bot.db.fetchrow("SELECT * FROM levelsetup WHERE guild_id = $1", ctx.guild.id)
   if not check: 
    await ctx.warn(f"Leveling is not enabled")
    return False
   return True
  return commands.check(predicate)

def is_reskin():
 async def predicate(ctx: commands.Context): 
  check = await ctx.bot.db.fetchrow("SELECT * FROM reskin_toggle WHERE guild_id = $1", ctx.guild.id)
  if not check: await ctx.warn("Reskin is **not** enabled")
  return check is not None 
 return commands.check(predicate)