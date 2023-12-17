import discord, time
from discord.ext import commands

class info(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
    
    @commands.command(description="check bot's latency", help="info")
    async def ping(self, ctx):
      await ctx.neutral(f"latency `{round(self.bot.latency * 1000)}ms`", emoji="🛰")
    
    @commands.command(description="check bot's uptime", help="info")
    async def uptime(self, ctx):
      return await ctx.neutral(f"**{self.bot.user.name}** is running for **{self.bot.ext.uptime}**", emoji="⏰")
    
    @commands.command(description="check bots information", aliases=["bi", "info", "about"], help="info")
    async def botinfo(self, ctx):
      embed = discord.Embed(color=self.bot.color, description=f"Easy-to-use multi-purpose discord bot made by [**stand**](https://discord.com/users/1074668481867419758)\nMonitoring **{self.bot.ext.human_format(sum(g.member_count for g in self.bot.guilds))}** users in over **{len(self.bot.guilds)}** servers").add_field(name="stats", value=f"**commands:** {len(self.bot.commands)}\n**ping:** `{round(self.bot.latency * 1000)}ms`\n**dpy:** {discord.__version__}").set_author(name=self.bot.user.name, icon_url=self.bot.user.display_avatar.url).set_footer(text=f"online for {self.bot.ext.uptime}")
      await ctx.reply(embed=embed)
    
    @commands.command(description="invite the bot", aliases=["inv", "support"])
    async def invite(self, ctx):
      view = discord.ui.View()
      view.add_item(discord.ui.Button(label=f"invite {self.bot.user.name}", url=f"https://discord.com/api/oauth2/authorize?client_id={self.bot.user.id}&permissions=8&scope=bot%20applications.commands"))
      view.add_item(discord.ui.Button(label="support", url="https://discord.gg/DX4MxrxsCg"))
      await ctx.send(view=view)
    
async def setup(bot):
    await bot.add_cog(info(bot))