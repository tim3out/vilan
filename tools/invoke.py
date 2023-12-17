import discord
from discord.ext import commands
from .embed import EmbedBuilder
from typing import Union

class Invoke:
 
 async def invoke_send(ctx: commands.Context, member: Union[discord.User, discord.Member], reason: str): 
  res = await ctx.bot.db.fetchrow("SELECT embed FROM invoke WHERE guild_id = $1 AND command = $2", ctx.guild.id, ctx.command.name)
  if res: 
     code = res['embed']
     try: 
      x = await EmbedBuilder.to_object(EmbedBuilder.embed_replacement(member, Invoke.invoke_replacement(member, code.replace("{reason}", reason))))
      await ctx.reply(content=x[0], embed=x[1], view=x[2])
     except: await ctx.reply(EmbedBuilder.embed_replacement(member, Invoke.invoke_replacement(member, code.replace("{reason}", reason)))) 
     return True 
  return False   
 
 def invoke_replacement(member: Union[discord.Member, discord.User], params: str=None):
  if params is None: return None
  if '{member}' in params: params=params.replace("{member}", str(member))
  if '{member.id}' in params: params=params.replace('{member.id}', str(member.id))
  if '{member.name}' in params: params=params.replace('{member.name}', member.name)
  if '{member.mention}' in params: params=params.replace('{member.mention}', member.mention)
  if '{member.discriminator}' in params: params=params.replace('{member.discriminator}', member.discriminator)
  if '{member.avatar}' in params: params=params.replace('{member.avatar}', member.display_avatar.url)
  return params

 async def invoke_cmds(ctx: commands.Context, member: Union[discord.Member, discord.User], embed: str) -> discord.Message:
  res = await ctx.bot.db.fetchrow("SELECT embed FROM invoke WHERE guild_id = $1 AND command = $2", ctx.guild.id, ctx.command.name)
  if res:
   code = res['embed']    
   if embed == "none": 
    await ctx.bot.db.execute("DELETE FROM invoke WHERE guild_id = $1 AND command = $2", ctx.guild.id, ctx.command.name)
    return await ctx.approve(f"Deleted the custom response for **{ctx.command.name}**")
   elif embed == "view": 
    em = discord.Embed(color=ctx.bot.color, title=f"invoke {ctx.command.name} message", description=f"```{code}```")
    return await ctx.reply(embed=em)
   elif embed == code: return await ctx.warn(f"This embed is already **configured** as the {ctx.command.name} custom response")
   else:
      await ctx.bot.db.execute("UPDATE invoke SET embed = $1 WHERE guild_id = $2 AND command = $3", embed, ctx.guild.id, ctx.command.name)
      return await ctx.approve(f"Updated your custom **{ctx.command.name}** message to {'the embed' if '--embed' in embed else ''}\n```{embed}```")
  else: 
   await ctx.bot.db.execute("INSERT INTO invoke VALUES ($1,$2,$3)", ctx.guild.id, ctx.command.name, embed)
   return await ctx.approve(f"Added your custom **{ctx.command.name}** message to {'the embed' if '--embed' in embed else ''}\n```{embed}```")