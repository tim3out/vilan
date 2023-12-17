import discord, os, asyncio
from discord.ext import commands
from tools.embed import EmbedBuilder

class Ticket(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
    
    @commands.group(invoke_without_command=True)
    async def ticket(self, ctx):
      await ctx.create_pages()
    
    @ticket.command(description="configure the ticket message", help="config", usage="[message]")
    @commands.has_permissions("administrator")
    async def message(self, ctx: commands.Context, *, message: str=None):
        check = await self.bot.db.execute("SELECT * FROM tickets WHERE guild_id = $1", ctx.guild.id)
        if message:
         if not check: await self.bot.db.execute("INSERT INTO tickets (guild_id, message) VALUES ($1,$2)", ctx.guild.id, message)
         else: await self.bot.db.execute("UPDATE tickets SET message = $1 WHERE guild_id = $2", message, ctx.guild.id)
         return await ctx.approve(f"Ticket message set to\n```{message}```")
        else:
          if not check: return await ctx.warn("No custom ticket message found")
          else: await self.bot.db.execute("UPDATE tickets SET message = $1 WHERE guild_id = $2", None, ctx.guild.id)
          return await ctx.approve("Ticket message set to default")
    
    @ticket.command(description="configure the ticket opening message", help="config", usage="[message]")
    @commands.has_permissions("administrator")
    async def opened(self, ctx: commands.Context, *, message: str=None):
        check = await self.bot.db.execute("SELECT * FROM tickets WHERE guild_id = $1", ctx.guild.id)
        if message:
         if not check: await self.bot.db.execute("INSERT INTO tickets (guild_id, opened) VALUES ($1,$2)", ctx.guild.id, message)
         else: await self.bot.db.execute("UPDATE tickets SET opened = $1 WHERE guild_id = $2", message, ctx.guild.id)
         return await ctx.approve(f"Ticket opening message set to\n```{message}```")
        else:
          if not check: return await ctx.warn("No custom ticket opening message found")
          else: await self.bot.db.execute("UPDATE tickets SET opened = $1 WHERE guild_id = $2", None, ctx.guild.id)
          return await ctx.approve("Ticket opening message set to default")
    
    @ticket.command(description="set ticket category", help="config", usage="[category]")
    @commands.has_permissions("administrator")
    async def category(self, ctx: commands.Context, *, channel: discord.CategoryChannel=None):
        check = await self.bot.db.fetchrow("SELECT * FROM tickets WHERE guild_id = $1", ctx.guild.id)
        if channel:
         if not check: await self.bot.db.execute("INSERT INTO tickets (guild_id, category) VALUES ($1,$2)", ctx.guild.id, channel.id)
         else: await self.bot.db.execute("UPDATE tickets SET category = $1 WHERE guild_id = $2", channel.id, ctx.guild.id)
         return await ctx.approve("Ticket category set to {}".format(channel.mention))
        else:
          if not check: return await ctx.warn("No ticket category found")
          else: await self.bot.db.execute("UPDATE tickets SET category = $1 WHERE guild_id = $2", None, ctx.guild.id)
          return await ctx.approve("Removed ticket category")
    
    @ticket.command(description="configure the ticket channel", help="config", usage="[channel]")
    @commands.has_permissions("administrator")
    async def channel(self, ctx: commands.Context, *, channel: discord.TextChannel=None):
        check = await self.bot.db.fetchrow("SELECT * FROM tickets WHERE guild_id = $1", ctx.guild.id)
        if channel:
         if not check: await self.bot.db.execute("INSERT INTO tickets (guild_id, channel_id) VALUES ($1,$2)", ctx.guild.id, channel.id)
         else: await self.bot.db.execute("UPDATE tickets SET channel_id = $1 WHERE guild_id = $2", channel.id, ctx.guild.id)
         return await ctx.approve("Ticket channel set to {}".format(channel.mention))
        else:
          if not check: return await ctx.warn("No ticket channel found")
          else: await self.bot.db.execute("UPDATE tickets SET channel_id = $1 WHERE guild_id = $2", None, ctx.guild.id)
          return await ctx.approve("Removed ticket channel")
    
    @ticket.command(description="configure the ticket logging channel", help="config", usage="[channel]")
    @commands.has_permissions("administrator")
    async def logs(self, ctx: commands.Context, *, channel: discord.TextChannel=None):
        check = await self.bot.db.fetchrow("SELECT * FROM tickets WHERE guild_id = $1", ctx.guild.id)
        if channel:
         if not check: await self.bot.db.execute("INSERT INTO tickets (guild_id, logs) VALUES ($1,$2)", ctx.guild.id, channel.id)
         else: await self.bot.db.execute("UPDATE tickets SET logs = $1 WHERE guild_id = $2", channel.id, ctx.guild.id)
         return await ctx.approve("Ticket logs set to {}".format(channel.mention))
        else:
          if not check: return await ctx.warn("No ticket logs found")
          else: await self.bot.db.execute("UPDATE tickets SET logs = $1 WHERE guild_id = $2", None, ctx.guild.id)
          return await ctx.approve("Removed tickeg logs")
    
    @ticket.command(description="send the ticket panel", help="config")
    @commands.has_permissions("administrator")
    async def send(self, ctx: commands.Context):
        check = await self.bot.db.fetchrow("SELECT * FROM tickets WHERE guild_id = $1", ctx.guild.id)
        if not check: return await ctx.send_warning("No ticket panel found")
        if not ctx.guild.get_channel(check["channel_id"]): return await ctx.warn("Channel not found")
        channel = ctx.guild.get_channel(check["channel_id"])
        message = None
        if check["message"]:
         view = CreateTicket()
         try:
           x = await EmbedBuilder.to_object(EmbedBuilder.embed_replacement(ctx.author, check['message']))
           message = await channel.send(content=x[0], embed=x[1], view=view)
         except: message = await channel.send(EmbedBuilder.embed_replacement(ctx.author, check['message']), view=view)
        else:
          embed = discord.Embed(color=self.bot.color, title="Create a ticket", description="Click on the button below to create a ticket")
          embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar.url)
          message = await channel.send(embed=embed, view=CreateTicket())
          await ctx.approve("Ticket message sent to {}".format(channel.mention))

    @ticket.command(description="check the ticket panel settings", help="config")
    @commands.has_permissions("administrator")
    async def settings(self, ctx: commands.Context):
        check = await self.bot.db.fetchrow("SELECT * FROM tickets WHERE guild_id = $1", ctx.guild.id)
        if not check: return await ctx.warn("No ticket panel found")
        embed = discord.Embed(color=self.bot.color, title="ticket settings", description="settings for **{}**".format(ctx.guild.name))
        embed.add_field(name="channel", value=ctx.guild.get_channel(check["channel_id"]).mention if ctx.guild.get_channel(check["channel_id"]) else "none")
        embed.add_field(name="logs", value=ctx.guild.get_channel(check["logs"]).mention if ctx.guild.get_channel(check["logs"]) else "none")
        embed.add_field(name="category", value=ctx.guild.get_channel(check["category"]).mention if ctx.guild.get_channel(check["category"]) else "none")
        embed.add_field(name="message", value="```{}```".format(check["message"]) if check["message"] else "default", inline=False)
        await ctx.reply(embed=embed)
        
async def setup(bot):
    await bot.add_cog(Ticket(bot))