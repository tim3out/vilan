import discord, datetime
from discord.ext import commands
from discord import app_commands

class Cog(commands.Cog):
 def __init__(self, bot: commands.AutoShardedBot):
    self.bot = bot
 
 @app_commands.command(name="poll", description="create a poll")
 async def poll(self, ctx: discord.Interaction, question: str, first: str, second: str):
  embed = discord.Embed(color=ctx.client.color, title=question, description=f"1️⃣ - {first}\n\n2️⃣ - {second}")
  embed.set_footer(text=f"poll created by {ctx.user}")
  channel = self.bot.get_channel(ctx.channel.id)
  await ctx.response.send_message('poll sent', ephemeral=True)
  mes = await channel.send(embed=embed)
  emoji1 = '1️⃣'
  emoji2 = '2️⃣'
  await mes.add_reaction(emoji1)
  await mes.add_reaction(emoji2)    

async def setup(bot) -> None:
    await bot.add_cog(Cog(bot))    