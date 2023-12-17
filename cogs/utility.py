from discord import Embed, Member, User, TextChannel, Spotify, Role, File
from discord.ext.commands import command, Context, Cog, AutoShardedBot as Bot, group, Author, hybrid_command
import discord, datetime, io, colorgram
from typing import Union
from handlers.lastfmhandler import Handler
from discord.ui import View, Button
from shazamio import Shazam, Serialize
from PIL import Image
from io import BytesIO

DISCORD_API_LINK = "https://discord.com/api/invite/"

class utility(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.lastfmhandler = Handler("332df3ed98bc15dc70f8166fdcd74f87")
    
    command(description="get a bot information", help="utility", usage="[id]")
    async def app(self, ctx: Context, id: int):
      data = await self.bot.session.json(f"https://discord.com/api/applications/{id}")
      embed = Embed(color=self.bot.color, title=f"{data['bot']['username']}'s info", description=f"{data['description']}").add_field(name="stats", value=f"**application owner:** {data['owner']['username']}\n**application id:** {data['bot']['id']}\n**public**: {'Yes' if data['bot_public'] == True else 'No'}\n**require code grant:** {'Yes' if data['bot_require_code_grant'] == True else 'No'}\n**permissions:** {data['install_params']['permissions']}\n**guilds:** {data['approximate_guild_count']}").set_thumbnail(url=f"https://cdn.discordapp.com/avatars/{id}/{data['bot']['avatar']}.png")
      await ctx.reply(embed=embed)
    
    @hybrid_command(description="get someone's snapchat stories", help="utility", usage="[username]", aliases=["snapstory"])
    async def snapchatstory(self, ctx: Context, *, name: str):
      data = await self.bot.session.json("https://api.pretend.space/snapstory", params={"username": name}, headers={"Authorization": f"Bearer {self.bot.pretend_api}"})
      if data.get('detail'): return await ctx.error("Account not found or story not found")
      embeds = []
      for story in data['stories']:
        embed = Embed(color=self.bot.color).set_image(url=f"{story['url']}")
        embeds.append(embed)
      await ctx.paginate(embeds)
    
    @command(description="see an user avatar history", usage="<member>", aliases=["avh"], help="utility")
    async def avatarhistory(self, ctx: Context, *, member: Member=Author):
      return await ctx.neutral(f"check **{member}'s** past [**avatars**](https://pretend.space/avatars/{member.id})")
    
    @hybrid_command(description="get a member's bio", usage="<member>", help="utility")
    async def bio(self, ctx: Context, *, member: Member=Author):
      r = await self.bot.session.get(f"https://discord.com/api/v10/users/{member.id}/profile", headers={"Authorization": self.bot.random_token})
      embed = Embed(color=self.bot.color, description=f"{r['user']['bio']}").set_author(name=f"{member.name}'s about me", icon_url=member.display_avatar.url)
      return await ctx.reply(embed=embed)
    
    @command(description="get the dominant color from an image", usage="[image url]", help="utility")
    async def dominant(self, ctx: Context):
      if not ctx.message.attachments: return await ctx.warn("Please provide an image")
      img = Image.open(io.BytesIO(await ctx.message.attachments[0].read()))
      img.thumbnail((32, 32))   
      colors = colorgram.extract(img, 3)
      rgb = colors[0].rgb
      hexx = discord.Color.from_rgb(r=rgb.r, g=rgb.g, b=rgb.b)
      hex_color = hex(hexx.value)
      color = int(hex_color, 16)
      await ctx.reply(embed=discord.Embed(color=self.bot.color).add_field(name="RGB", value=f"rgb({rgb.r}, {rgb.g}, {rgb.b})").add_field(name="HEX", value=f"{hex_color}"))
    
    @command(description="identify a song from audio", usage="[attachment]", help="utility")
    async def shazam(self, ctx: Context):
      if not ctx.message.attachments: return await ctx.warn("Please provide a video")
      song = await Shazam().recognize_song(await ctx.message.attachments[0].read())
      await ctx.neutral(f"Found [{song['track']['share']['text']}]({song['track']['share']['href']})", emoji="<:shazam:1133831097445269504>")
    
    @hybrid_command(description="get someone's instagram profile informations", usage="[username]", aliases=["ig"], help="utility")
    async def instagram(self, ctx: Context, *, name: str):
        data = await self.bot.session.json("https://api.pretend.space/instagram", params={"username": name}, headers={"Authorization": f"Bearer {self.bot.pretend_api}"})
        await ctx.typing()
        if data.get('detail'): return await ctx.error("Account not found")
        embed = Embed(color=self.bot.color, description=f"**[@{name}]({data['url']}) {'<:verified:1140291032987213945>' if data.get('is_verified') else ''} {'🔒' if data.get('is_private') else ''} {'💼' if data.get('is_bussines_account') else ''}**\n{data['bio']}")
        embed.add_field(name="following", value=data["following"])
        embed.add_field(name="followers", value=data["followers"])
        embed.add_field(name="posts", value=data["posts"])
        embed.set_thumbnail(url=data["avatar"])
        await ctx.reply(embed=embed)
    
    @hybrid_command(description="get someone's tiktok profile informations", usage="[username]", aliases=["tt"], help="utility")
    async def tiktok(self, ctx: Context, *, name: str):
        data = await self.bot.session.json("https://api.pretend.space/tiktok", params={"username": name}, headers={"Authorization": f"Bearer {self.bot.pretend_api}"})
        await ctx.typing()
        if data.get('detail'): return await ctx.error("Account not found")
        embed = Embed(color=self.bot.color, description=f"**[{data['username']}]({data['url']}) {'<:verified:1140291032987213945>' if data.get('verified') else ''} {'🔒' if data.get('private') else ''}**\n{data['bio']}")
        embed.add_field(name="following", value=data["following"])
        embed.add_field(name="followers", value=data["followers"])
        embed.add_field(name="hearts", value=data["hearts"])
        embed.set_thumbnail(url=data["avatar"])
        await ctx.reply(embed=embed)
    
    @command(description="search for images on google", usage="[query]", aliases=["img", "google"], help="utility")
    async def image(self, ctx: Context, *, query: str):
      embeds = []
      data = await self.bot.session.json("https://notsobot.com/api/search/google/images", params={"query": query, "safe": "True"})
      for item in data: embeds.append(Embed(color=self.bot.color, title=f"<:google:1133832005184913529> Search results for {query}", description=item['header'], url=item['url']).set_image(url=item['image']['url']).set_footer(text=f"(Safe Search active)").set_author(name=ctx.author.global_name if ctx.author.global_name else ctx.author.name, icon_url=ctx.author.display_avatar.url))
      await ctx.paginate(embeds)
    
    @command(description="translate a word in any language you want", usage="[language] [text]", aliases=["tr"], help="utility")
    async def translate(self, ctx: Context, lang: str, *, text: str):
        data = (await self.bot.session.json("https://api.pretend.space/translate", params={"language": lang, "text": text}, headers={"Authorization": f"Bearer {self.bot.pretend_api}"}))
        await ctx.reply(embed=Embed(color=self.bot.color, title=f"translated to {data['language']}", description=f"{data['translated']}", timestamp=datetime.datetime.now()))
    
    @hybrid_command(description="view a user avatar", aliases=['av'], help="utility")
    async def avatar(self, ctx, *, user: Union[User, Member]=Author):
      embed = discord.Embed(description=f"{user.name}'s avatar")
      embed.set_image(url=user.display_avatar)
      await ctx.send(embed=embed)
    
    @command(description="gets the invite link with administrator permission of a bot", usage="[bot id]", help="utility")
    async def getbotinvite(self, ctx, id: User):   
      if not id.bot: return await ctx.error("This is not a bot")
      view = discord.ui.View()
      view.add_item(discord.ui.Button(label=f"invite {id.name}", url=f"https://discord.com/api/oauth2/authorize?client_id={id.id}&permissions=8&scope=bot%20applications.commands"))
      await ctx.reply(view=view)
    
    @command(description="get the first message from a channel", usage="<channel>", aliases=["firstmsg"], help="utility")
    async def firstmessage(self, ctx: Context, *, channel: TextChannel=None):
        channel = channel or ctx.channel
        messages = [mes async for mes in channel.history(oldest_first=True, limit=1)]
        message = messages[0]
        embed = Embed(color=self.bot.color, title="first message in {}".format(channel), description=message.content, timestamp=message.created_at)
        embed.set_author(name=message.author.name, icon_url=message.author.display_avatar.url)
        view = View()
        view.add_item(Button(label="message", url=message.jump_url))
        await ctx.reply(embed=embed, view=view)
    
    @hybrid_command(description="show users information", usage="<user>", aliases=["ui"], help="utility")
    async def userinfo(self, ctx, *, member: User=Author):
      user = await self.bot.fetch_user(member.id)
      badges = []
      if user.public_flags.active_developer: 
       badges.append("<:activdev:1138838730115928155>")
      if user.public_flags.early_supporter:
       badges.append("<:supporter:1138838928867217569>")
      if user.public_flags.verified_bot_developer:
       badges.append("<:developer:1138838866493710446>")
      if user.public_flags.staff: 
       badges.append("<:staff:1138838822260588694>")
      if user.public_flags.bug_hunter:
       badges.append("<:bughunter:1120024676157100162>") 
      if user.public_flags.bug_hunter_level_2:
       badges.append("<:gold_bughunter:1120024742569726102>")   
      if user.public_flags.partner:
       badges.append("<:partener:1120024599040622725>")
      if user.public_flags.discord_certified_moderator:
       badges.append("<:moderator_programs:1138838269816221696>")
      if user.public_flags.hypesquad_bravery:
       badges.append("<:bravery:1138839692524126350>")
      if user.public_flags.hypesquad_balance:
       badges.append("<:balanced:1138839222950826054>")
      if user.public_flags.hypesquad_brilliance:
       badges.append("<:brilliance:1138839114997829712>")  
      if user.display_avatar.is_animated() or user.banner is not None:
       badges.append("<:nitro:1138847230552457320>")
      if user.discriminator == "0":
       badges.append("<:pomelo:1138838428369289227>")

      for guild in self.bot.guilds: 
       mem = guild.get_member(user.id)
       if mem:
        if mem.premium_since:
         badges.append("<:boost:1138839054796988427>")
         break
      
      async def lf(mem: Union[Member, User]): 
        check = await self.bot.db.fetchrow("SELECT username FROM lastfm WHERE user_id = {}".format(mem.id))
        if check: 
          u = str(check['username']) 
          if u != "error": 
            a = await self.lastfmhandler.get_tracks_recent(u, 1)
            return f"<:lastfm:1138839782408060978> Listening to [{a['recenttracks']['track'][0]['name']}]({a['recenttracks']['track'][0]['url']}) by **{a['recenttracks']['track'][0]['artist']['#text']}** on lastfm"
      
        return ""
      
      e = Embed(color=self.bot.color, title="‎" + "".join(map(str, badges)), description=f"{await lf(member)}")
      e.set_author(name=member.global_name if member.global_name else member.name, icon_url=member.display_avatar.url)
      e.set_thumbnail(url=member.display_avatar.url)
      e.add_field(name="dates", value=f"**joined:** <t:{int(member.joined_at.timestamp())}:R>\n**created:** <t:{int(member.created_at.timestamp())}:R>")
      roles = member.roles[1:][::-1]
      if len(roles) > 0: e.add_field(name=f"roles ({len(roles)})", value=' '.join([r.mention for r in roles]) if len(roles) < 5 else ' '.join([r.mention for r in roles[:4]]) + f" and {len(roles)-4} more")
      e.set_footer(text=f"ID: {str(member.id)}")
      return await ctx.reply(embed=e)
    
    @command(description="get role informations", help="utility", usage="[role]", aliases=["ri"])
    async def roleinfo(self, ctx: Context, *, role: Union[Role, str]): 
      if isinstance(role, str): 
        role = ctx.find_role(role)
        if not role: return await ctx.warn(f"**{role.name}** is not a valid role")
            
      embed = Embed(color=role.color, title="@{} - `{}`".format(role.name, role.id), timestamp=role.created_at)
      embed.set_thumbnail(url=role.display_icon if not isinstance(role.display_icon, str) else None)
      embed.add_field(name="stats", value=f"**hoist:** {str(role.hoist).lower()}\n**mentionable:** {str(role.mentionable).lower()}\n**members:** {str(len(role.members))}")
      await ctx.reply(embed=embed)
    
    @command(description="show information about an invite", usage="[invite code]", aliases=["ii"], help="utility")
    async def inviteinfo(self, ctx: Context, code: str):
        data = await self.bot.session.json(DISCORD_API_LINK + code, proxy=self.bot.proxy_url, ssl=False)
        name = data['guild']['name']
        id = data['guild']['id']
        description = data['guild']["description"]
        boosts = data["guild"]["premium_subscription_count"]
        avatar = f"https://cdn.discordapp.com/icons/{data['guild']['id']}/{data['guild']['icon']}.{'gif' if 'a_' in data['guild']['icon'] else 'png'}?size=1024"
        embed = Embed(color=self.bot.color, description=f"{description}").set_thumbnail(url=avatar).set_author(name=f"{name}").set_footer(text=f"ID: {id}")
        embed.add_field(name="info", value=f"<:boosts:1133831284553162882> **boosts:** {boosts}")
        await ctx.reply(embed=embed)
    
    @command(aliases=["s"], description="check the latest deleted message from a channel", help="utility")
    async def snipe(self, ctx: Context, *, number: int=1):
        check = await self.bot.db.fetch("SELECT * FROM snipe WHERE guild_id = {} AND channel_id = {}".format(ctx.guild.id, ctx.channel.id))
        if len(check) == 0: return await ctx.warn("No deleted messages found in this channel") 
        if number > len(check): return await ctx.warn(f"snipe limit is **{len(check)}**".capitalize()) 
        sniped = check[::-1][number-1]
        em = Embed(color=self.bot.color, description=sniped['content'], timestamp=sniped['time'])
        em.set_author(name=sniped['author'], icon_url=sniped['avatar']) 
        em.set_footer(text="{}/{}".format(number, len(check)))
        if sniped['attachment'] != "none":
         if ".mp4" in sniped['attachment'] or ".mov" in sniped['attachment']:
          url = sniped['attachment']
          r = await self.bot.session.read(url)
          bytes_io = BytesIO(r)
          file = File(fp=bytes_io, filename="video.mp4")
          return await ctx.reply(embed=em, file=file)
         else:
           try: em.set_image(url=sniped['attachment'])
           except: pass 
        return await ctx.reply(embed=em)
    
    @hybrid_command(description="check how many members does your guild has", aliases=["mc"], help="utility")
    async def membercount(self, ctx: Context):
      b=len(set(b for b in ctx.guild.members if b.bot))
      h=len(set(b for b in ctx.guild.members if not b.bot))
      embed = Embed(color=self.bot.color)
      embed.set_author(name=f"{ctx.guild.name}'s member count", icon_url=ctx.guild.icon)
      embed.add_field(name=f"members +{len([m for m in ctx.guild.members if (datetime.datetime.now() - m.joined_at.replace(tzinfo=None)).total_seconds() < 3600*24 and not m.bot])}", value=h)
      embed.add_field(name="total", value=ctx.guild.member_count) 
      embed.add_field(name="bots", value=b)
      await ctx.reply(embed=embed)
    
    @command(description="see all banned members", help="utility")
    async def bans(self, ctx: Context): 
     banned = [m async for m in ctx.guild.bans()]
     if len(banned) == 0: return await ctx.warn("There are no banned people here")
     i=0
     k=1
     l=0
     mes = ""
     number = []
     messages = []
     for m in banned: 
       mes = f"{mes}`{k}` **{m.user}** - `{m.reason or 'No reason provided'}` \n"
       k+=1
       l+=1
       if l == 10:
        messages.append(mes)
        number.append(Embed(color=self.bot.color, title=f"banned ({len(banned)})", description=messages[i]))
        i+=1
        mes = ""
        l=0
    
     messages.append(mes)
     number.append(Embed(color=self.bot.color, title=f"banned ({len(banned)})", description=messages[i]))
     await ctx.paginate(number)
    
    @hybrid_command(description="clear the guilds snipes", help="utility", aliases=["cs"])
    async def clearsnipes(self, ctx: Context):
      lis = ["snipe"]
      for l in lis: await self.bot.db.execute(f"DELETE FROM {l}")
      return await ctx.approve("Cleared the guild snipes")
    
async def setup(bot):
    await bot.add_cog(utility(bot))