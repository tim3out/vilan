import os, dotenv, discord
from discord.ext import commands
from tools.bot import vilan
dotenv.load_dotenv(verbose=True)

bot = vilan()

@bot.check 
async def blacklist(ctx: commands.Context):
 if not ctx.guild: return False
 check = await bot.db.fetchrow("SELECT * FROM nodata WHERE user_id = $1", ctx.author.id)
 if check: 
  if check["state"] == "false": return False 
 return check is None

@bot.check 
async def gblacklist(ctx: commands.Context):
 if not ctx.guild: return False
 check = await bot.db.fetchrow("SELECT * FROM nodata WHERE guild_id = $1", ctx.guild.id)
 if check:
  if check["state"] == "false": return False 
 return check is None

@bot.check
async def disabled_command(ctx: commands.Context):
  cmd = bot.get_command(ctx.invoked_with)
  if not cmd: return True
  check = await ctx.bot.db.fetchrow('SELECT * FROM disablecommand WHERE command = $1 AND guild_id = $2', cmd.name, ctx.guild.id)
  if check: await bot.ext.error(ctx, f"**{cmd.name}** is **disabled** in this server")
  return check is None

if __name__ == '__main__':
    bot.run(os.environ["token"])