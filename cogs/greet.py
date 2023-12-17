import discord
from discord.ext import commands
from tools.embed import EmbedBuilder

class greet(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot 
    
    @commands.group(invoke_without_command=True)
    async def boost(self, ctx): 
     await ctx.create_pages()

    @boost.command(name="variables", help="config", description="return the variables for the boost message")
    async def boost_variables(self, ctx: commands.Context): 
      await ctx.invoke(self.bot.get_command('variables'))
     
    @boost.command(name="config", help="config", description="returns stats of the boost message")
    async def boost_config(self, ctx: commands.Context): 
     check = await self.bot.db.fetchrow("SELECT * FROM boost WHERE guild_id = $1", ctx.guild.id)
     if not check: return await ctx.warn("Boost is **not** configured")
     channel = f'#{ctx.guild.get_channel(check["channel_id"]).name}' if ctx.guild.get_channel(check['channel_id']) else "none"
     e = check['mes'] or "none"
     embed = discord.Embed(color=self.bot.color, title=f"channel {channel}", description=f"```{e}```")
     await ctx.reply(embed=embed)     
    
    @boost.command(name="channel", description="configure the boost channel", help="config", usage="[channel]", brief="manage server")
    @commands.has_permissions("manage_guild")
    async def boost_channel(self, ctx: commands.Context, *, channel: discord.TextChannel=None):
      check = await self.bot.db.fetchrow("SELECT channel_id FROM boost WHERE guild_id = $1", ctx.guild.id)
      if check: await self.bot.db.execute("UPDATE boost SET channel_id = $1 WHERE guild_id = $2", channel.id, ctx.guild.id)
      else: await self.bot.db.execute("INSERT INTO boost VALUES ($1,$2,$3)", ctx.guild.id, channel.id, None)
      return await ctx.approve(f"Boost channel set to {channel.mention}")
    
    @boost.command(name="message", help="config", description="configure the boost message", usage="[message]", brief="manage server")
    @commands.has_permissions("manage_guild")
    async def boost_message(self, ctx: commands.Context, *, code: str):
      check = await self.bot.db.fetchrow("SELECT * FROM boost WHERE guild_id = $1", ctx.guild.id)
      if check: await self.bot.db.execute("UPDATE boost SET message = $1 WHERE guild_id = $2", code, ctx.guild.id)
      else: await self.bot.db.execute("INSERT INTO boost VALUES ($1,$2,$3)", ctx.guild.id, 0, code)
      return await ctx.approve(f"Boost message configured as\n```{code}```")
    
    @boost.command(name="delete", help="config", description="delete the boost module", brief="manage server")
    @commands.has_permissions("manage_guild")
    async def boost_delete(self, ctx: commands.Context):
      check = await self.bot.db.fetchrow("SELECT * FROM boost WHERE guild_id = $1", ctx.guild.id)
      if not check: return await ctx.warn("Boost is **not** configured")
      else: await self.bot.db.execute("DELETE FROM boost WHERE guild_id = $1", ctx.guild.id)
      return await ctx.approve("Boost has been **deleted**")
    
    @boost.command(name="test", help="config", description="test the boost module", brief="manage server")
    @commands.has_permissions("manage_guild")
    async def boost_test(self, ctx: commands.Context): 
      res = await self.bot.db.fetchrow("SELECT * FROM boost WHERE guild_id = $1", ctx.guild.id)
      if res: 
       channel = ctx.guild.get_channel(res['channel_id'])
       if channel is None: return await ctx.error("Channel **not** found")
       try: 
        x=await EmbedBuilder.to_object(EmbedBuilder.embed_replacement(ctx.author, res['message']))
        await channel.send(content=x[0],embed=x[1], view=x[2])
       except: await channel.send(EmbedBuilder.embed_replacement(ctx.author, res['message'])) 
       await ctx.approve("Sent the **boost** message to {}".format(channel.mention))
    
    @commands.group(invoke_without_command=True)
    async def leave(self, ctx): 
     await ctx.create_pages()

    @leave.command(name="variables", help="config", description="return the variables for the leave message")
    async def leave_variables(self, ctx: commands.Context): 
      await ctx.invoke(self.bot.get_command('variables'))
     
    @leave.command(name="config", help="config", description="returns stats of the leave message")
    async def leave_config(self, ctx: commands.Context): 
     check = await self.bot.db.fetchrow("SELECT * FROM leave WHERE guild_id = $1", ctx.guild.id)
     if not check: return await ctx.warn("Welcome is **not** configured")
     channel = f'#{ctx.guild.get_channel(check["channel_id"]).name}' if ctx.guild.get_channel(check['channel_id']) else "none"
     e = check['mes'] or "none"
     embed = discord.Embed(color=self.bot.color, title=f"channel {channel}", description=f"```{e}```")
     await ctx.reply(embed=embed)     
    
    @leave.command(name="channel", description="configure the leave channel", help="config", usage="[channel]", brief="manage server")
    @commands.has_permissions("manage_guild")
    async def leave_channel(self, ctx: commands.Context, *, channel: discord.TextChannel=None):
      check = await self.bot.db.fetchrow("SELECT channel_id FROM leave WHERE guild_id = $1", ctx.guild.id)
      if check: await self.bot.db.execute("UPDATE leave SET channel_id = $1 WHERE guild_id = $2", channel.id, ctx.guild.id)
      else: await self.bot.db.execute("INSERT INTO leave VALUES ($1,$2,$3)", ctx.guild.id, channel.id, None)
      return await ctx.approve(f"Leave channel set to {channel.mention}")
    
    @leave.command(name="message", help="config", description="configure the leave message", usage="[message]", brief="manage server")
    @commands.has_permissions("manage_guild")
    async def leave_message(self, ctx: commands.Context, *, code: str):
      check = await self.bot.db.fetchrow("SELECT * FROM leave WHERE guild_id = $1", ctx.guild.id)
      if check: await self.bot.db.execute("UPDATE leave SET message = $1 WHERE guild_id = $2", code, ctx.guild.id)
      else: await self.bot.db.execute("INSERT INTO leave VALUES ($1,$2,$3)", ctx.guild.id, 0, code)
      return await ctx.approve(f"Leave message configured as\n```{code}```")
    
    @leave.command(name="delete", help="config", description="delete the leave module", brief="manage server")
    @commands.has_permissions("manage_guild")
    async def leave_delete(self, ctx: commands.Context):
      check = await self.bot.db.fetchrow("SELECT * FROM leave WHERE guild_id = $1", ctx.guild.id)
      if not check: return await ctx.warn("Leave is **not** configured")
      else: await self.bot.db.execute("DELETE FROM leave WHERE guild_id = $1", ctx.guild.id)
      return await ctx.approve("Leave has been **deleted**")
    
    @leave.command(name="test", help="config", description="test the leave module", brief="manage server")
    @commands.has_permissions("manage_guild")
    async def leave_test(self, ctx: commands.Context): 
      res = await self.bot.db.fetchrow("SELECT * FROM leave WHERE guild_id = $1", ctx.guild.id)
      if res: 
       channel = ctx.guild.get_channel(res['channel_id'])
       if channel is None: return await ctx.error("Channel **not** found")
       try: 
        x=await EmbedBuilder.to_object(EmbedBuilder.embed_replacement(ctx.author, res['message']))
        await channel.send(content=x[0],embed=x[1], view=x[2])
       except: await channel.send(EmbedBuilder.embed_replacement(ctx.author, res['message'])) 
       await ctx.approve("Sent the **leave** message to {}".format(channel.mention))
    
    @commands.group(aliases=["welc"], invoke_without_command=True)
    async def welcome(self, ctx): 
     await ctx.create_pages()

    @welcome.command(name="variables", help="config", description="return the variables for the welcome message")
    async def welcome_variables(self, ctx: commands.Context): 
      await ctx.invoke(self.bot.get_command('variables'))
     
    @welcome.command(name="config", help="config", description="returns stats of the welcome message")
    async def welcome_config(self, ctx: commands.Context): 
     check = await self.bot.db.fetchrow("SELECT * FROM welcome WHERE guild_id = $1", ctx.guild.id)
     if not check: return await ctx.warn("Welcome is **not** configured")
     channel = f'#{ctx.guild.get_channel(check["channel_id"]).name}' if ctx.guild.get_channel(check['channel_id']) else "none"
     e = check['mes'] or "none"
     embed = discord.Embed(color=self.bot.color, title=f"channel {channel}", description=f"```{e}```")
     await ctx.reply(embed=embed)     
    
    @welcome.command(name="channel", description="configure the welcome channel", help="config", usage="[channel]", brief="manage server")
    @commands.has_permissions("manage_guild")
    async def welcome_channel(self, ctx: commands.Context, *, channel: discord.TextChannel=None):
      check = await self.bot.db.fetchrow("SELECT channel_id FROM welcome WHERE guild_id = $1", ctx.guild.id)
      if check: await self.bot.db.execute("UPDATE welcome SET channel_id = $1 WHERE guild_id = $2", channel.id, ctx.guild.id)
      else: await self.bot.db.execute("INSERT INTO welcome VALUES ($1,$2,$3)", ctx.guild.id, channel.id, None)
      return await ctx.approve(f"Welcome channel set to {channel.mention}")
    
    @welcome.command(name="message", help="config", description="configure the welcome message", usage="[message]", brief="manage server")
    @commands.has_permissions("manage_guild")
    async def welcome_message(self, ctx: commands.Context, *, code: str):
      check = await self.bot.db.fetchrow("SELECT * FROM welcome WHERE guild_id = $1", ctx.guild.id)
      if check: await self.bot.db.execute("UPDATE welcome SET message = $1 WHERE guild_id = $2", code, ctx.guild.id)
      else: await self.bot.db.execute("INSERT INTO welcome VALUES ($1,$2,$3)", ctx.guild.id, 0, code)
      return await ctx.approve(f"Welcome message configured as\n```{code}```")
    
    @welcome.command(name="delete", help="config", description="delete the welcome module", brief="manage server")
    @commands.has_permissions("manage_guild")
    async def welcome_delete(self, ctx: commands.Context):
      check = await self.bot.db.fetchrow("SELECT * FROM welcome WHERE guild_id = $1", ctx.guild.id)
      if not check: return await ctx.warn("Welcome is **not** configured")
      else: await self.bot.db.execute("DELETE FROM welcome WHERE guild_id = $1", ctx.guild.id)
      return await ctx.approve("Welcome has been **deleted**")
    
    @welcome.command(name="test", help="config", description="test welcome module", brief="manage server")
    @commands.has_permissions("manage_guild")
    async def welcome_test(self, ctx: commands.Context): 
      res = await self.bot.db.fetchrow("SELECT * FROM welcome WHERE guild_id = $1", ctx.guild.id)
      if res: 
       channel = ctx.guild.get_channel(res['channel_id'])
       if channel is None: return await ctx.error("Channel **not** found")
       try: 
        x=await EmbedBuilder.to_object(EmbedBuilder.embed_replacement(ctx.author, res['message']))
        await channel.send(content=x[0],embed=x[1], view=x[2])
       except: await channel.send(EmbedBuilder.embed_replacement(ctx.author, res['message'])) 
       await ctx.approve("Sent the **welcome** message to {}".format(channel.mention))
    
async def setup(bot):
    await bot.add_cog(greet(bot))