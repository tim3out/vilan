import discord
from discord.ext import commands

class guild(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel): 
      if isinstance(channel, discord.TextChannel): 
            check = await self.bot.db.fetchrow("SELECT * FROM opened_tickets WHERE guild_id = $1 AND channel_id = $2", channel.guild.id, channel.id)       
            if check is not None: await self.bot.db.execute("DELETE FROM opened_tickets WHERE guild_id = $1 AND channel_id = $2", channel.guild.id, channel.id)
    
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
      check = await self.bot.db.fetchrow("SELECT * FROM mod WHERE guild_id = {}".format(channel.guild.id))
      if check: await channel.set_permissions(channel.guild.get_role(int(check['role_id'])), view_channel=False, reason="overwriting permissions for jail role")

async def setup(bot):
    await bot.add_cog(guild(bot))