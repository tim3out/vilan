import discord
from discord.ext import commands
from typing import Union

class Whitelist: 
  async def whitelist_things(ctx: commands.Context, module: str, target: Union[discord.Member, discord.User, discord.TextChannel]): 
    check = await ctx.bot.db.fetchrow("SELECT * FROM whitelist WHERE guild_id = $1 AND module = $2 AND object_id = $3 AND mode = $4", ctx.guild.id, module, target.id, "user" if isinstance(target, discord.Member) or isinstance(target, discord.User) else "channel")
    if check: return await ctx.warn(f"{f'**{target}**' if isinstance(target, discord.Member) else target.mention} is **already** whitelisted for **{module}**")
    await ctx.bot.db.execute("INSERT INTO whitelist VALUES ($1,$2,$3,$4)", ctx.guild.id, module, target.id, "user" if isinstance(target, discord.Member) or isinstance(target, discord.User) else "channel")
    return await ctx.approve(f"{f'**{target}**' if isinstance(target, discord.Member) else target.mention} is now whitelisted for **{module}**")

  async def unwhitelist_things(ctx: commands.Context, module: str, target: Union[discord.Member, discord.TextChannel]): 
    check = await ctx.bot.db.fetchrow("SELECT * FROM whitelist WHERE guild_id = $1 AND module = $2 AND object_id = $3 AND mode = $4", ctx.guild.id, module, target.id, "user" if isinstance(target, discord.Member) or isinstance(target, discord.User) else "channel")
    if not check: return await ctx.warn(f"{f'**{target}**' if isinstance(target, discord.Member) else target.mention} is **not** whitelisted for **{module}**")
    await ctx.bot.db.execute("DELETE FROM whitelist WHERE guild_id = $1 AND module = $2 AND object_id = $3 AND mode = $4", ctx.guild.id, module, target.id, "user" if isinstance(target, discord.Member) or isinstance(target, discord.User) else "channel")
    return await ctx.approve(f"{f'**{target}**' if isinstance(target, discord.Member) else target.mention} has been unwhitelisted from **{module}**")

  async def whitelisted_things(ctx: commands.Context, module: str, target: str): 
   i=0
   k=1
   l=0
   mes = ""
   number = []
   messages = []  
   results = await ctx.bot.db.fetch("SELECT * FROM whitelist WHERE guild_id = $1 AND module = $2 AND mode = $3", ctx.guild.id, module, target)
   if len(results) == 0: return await ctx.warn(f"No whitelisted **{target}s** found for **{module}**")  
   for result in results:
    id = result['object_id'] 
    if target == "channel": mes = f"{mes}`{k}` {f'{ctx.guild.get_channel(id).mention} ({id})' if ctx.guild.get_channel(result['object_id']) is not None else result['object_id']}\n"
    else: mes = f"{mes} `{k}` {await ctx.bot.fetch_user(id)} ({id})\n"
    k+=1
    l+=1
    if l == 10:
     messages.append(mes)
     number.append(discord.Embed(color=ctx.bot.color, title=f"whitelisted {target}s ({len(results)})", description=messages[i]))
     i+=1
     mes = ""
     l=0
    
   messages.append(mes)  
   number.append(discord.Embed(color=ctx.bot.color, title=f"whitelisted {target}s ({len(results)})", description=messages[i]))
   await ctx.paginate(number)