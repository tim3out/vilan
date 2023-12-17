import discord, datetime, uwuipy
from discord.ext import commands
from tools.converters import Message

async def uwushit(bot, text: str) -> str:
    uwu = uwuipy.uwuipy()
    return uwu.uwuify(text)

class Messages(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        self._cd = commands.CooldownMapping.from_cooldown(3, 6, commands.BucketType.guild) 

    def get_ratelimit(self, message):
        bucket = self._cd.get_bucket(message)
        return bucket.update_rate_limit()
    
    @commands.Cog.listener('on_message')
    async def boost_listener(self, message: discord.Message): 
     if "MessageType.premium_guild" in str(message.type):
      if message.guild.id == 1132991358022467634: 
       member = message.author
       check = await self.bot.db.fetchrow("SELECT * FROM donor WHERE user_id = $1", member.id)
       if check: return 
       ts = int(datetime.datetime.now().timestamp())
       await self.bot.db.execute("INSERT INTO donor VALUES ($1,$2)", member.id, ts)  
       return await message.channel.send(f"{member.mention} enjoy your perks! <:joobiheart:1139786244973408307>")
    
    @commands.Cog.listener("on_message")
    async def reposter(self, message: discord.Message): 
      if not message.guild: return 
      if message.author.bot: return 
      args = message.content.split(" ")
      if (args[0] == f"{self.bot.user.name}"):
        url = args[1] 
        if "tiktok" in url:
         async with message.channel.typing(): 
          x = await self.bot.session.json("https://tikwm.com/api/", params={"url": url}) 
          video = x["data"]["play"]
          file = discord.File(fp=await self.bot.gbytes(video), filename=f"{self.bot.user.name}tiktok.mp4")
          embed = discord.Embed(color=self.bot.color, description=f"[{x['data']['title']}]({url})").set_author(name=f"@{x['data']['author']['unique_id']}", icon_url=x["data"]["author"]["avatar"])
          x = x["data"]
          embed.set_footer(text=f"❤ {self.bot.ext.human_format(x['digg_count'])}  💬 {self.bot.ext.human_format(x['comment_count'])}  🔗 {self.bot.ext.human_format(x['share_count'])}  👀 {self.bot.ext.human_format(x['play_count'])} | {message.author}", icon_url="https://media.discordapp.net/attachments/1060506008868376667/1124034551635771494/trapstar.png")
          await message.channel.send(embed=embed, file=file)
          try: await message.delete()
          except: pass
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
      if not message.guild: return
      if isinstance(message.author, discord.User): return
      check = await self.bot.db.fetchrow("SELECT * FROM uwulock WHERE guild_id = $1 AND user_id = $2", message.guild.id, message.author.id)
      if check:
        try: 
            await message.delete()
            uwumsg = await uwushit(self.bot, message.clean_content)
            webhooks = await message.channel.webhooks()
            if len(webhooks) == 0: webhook = await message.channel.create_webhook(name=f"{self.bot.user.name} - uwulock", reason="uwulock")
            else: webhook = webhooks[0] 
            await webhook.send(content=uwumsg, username=message.author.name, avatar_url=message.author.display_avatar.url)
        except: pass
    
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
     if not message.guild: return 
     if message.author.bot: return
     invites = ["discord.gg/", ".gg/", "discord.com/invite/"]
     if any(invite in message.content for invite in invites): return

     attachment = message.attachments[0].url if message.attachments else "none"
     author = str(message.author)
     content = message.content
     avatar = message.author.display_avatar.url 
     await self.bot.db.execute("INSERT INTO snipe VALUES ($1,$2,$3,$4,$5,$6,$7)", message.guild.id, message.channel.id, author, content, attachment, avatar, datetime.datetime.now())
  
    @commands.Cog.listener('on_message')
    async def on_autoresponder(self, message: discord.Message): 
     if Message.good_message(message): 
      res = await self.bot.db.fetchrow("SELECT response FROM autoresponder WHERE guild_id = $1 AND trigger = $2", message.guild.id, message.content)
      if res:
       retry_after = self.get_ratelimit(message)
       if retry_after: return
       reply = res['response']
       try: 
        x=await EmbedBuilder.to_object(EmbedBuilder.embed_replacement(message.author, reply))
        await message.channel.send(content=x[0],embed=x[1], view=x[2])
       except: await message.channel.send(EmbedBuilder.embed_replacement(message.author, reply))      
    
    @commands.Cog.listener('on_message')
    async def on_autoreact(self, message: discord.Message): 
     if Message.good_message(message): 
      check = await self.bot.db.fetchrow("SELECT emojis FROM autoreact WHERE guild_id = $1 AND trigger = $2", message.guild.id, message.content)
      if check: 
       retry_after = self.get_ratelimit(message)
       if retry_after: return
       emojis = json.loads(check['emojis'])   
       for emoji in emojis: 
         try: await message.add_reaction(emoji)
         except: continue
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message): 
      if "MessageType.premium_guild" in str(message.type):
       res = await self.bot.db.fetchrow("SELECT * FROM boost WHERE guild_id = $1", message.guild.id)
       if res: 
        channel = message.guild.get_channel(res['channel_id'])
        if channel is None: return 
        try: 
         x=await EmbedBuilder.to_object(EmbedBuilder.embed_replacement(message.author, res['message']))
         await channel.send(content=x[0],embed=x[1], view=x[2])
        except: await channel.send(EmbedBuilder.embed_replacement(message.author, res['message']))
    
async def setup(bot):
    await bot.add_cog(Messages(bot))