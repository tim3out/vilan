import os, sys, discord, string, random, json, time, datetime
from discord.ext import commands
from typing import List, Union
from .paginator import PgView
from math import floor, log

async def getprefix(bot, message):
    if not message.guild: return ";"
    res = await bot.db.fetchrow("SELECT * FROM prefixes WHERE guild_id = $1", message.guild.id) 
    if res: guildprefix = res["prefix"]
    else: guildprefix = ";"
    return guildprefix

def perms(perm: str=None):
   async def predicate(ctx: commands.Context):
    if not perm: return True 
    if ctx.guild.owner == ctx.author or ctx.author.guild_permissions.administrator: return True
    for r in ctx.author.roles:
     if perm in [str(p[0]) for p in r.permissions if p[1] is True]: return True 
     check = await ctx.bot.db.fetchrow("SELECT permissions FROM fake_perms WHERE role_id = $1 and guild_id = $2", r.id, r.guild.id)
     if not check: continue 
     if perm in json.loads(check[0]) or "administrator" in json.loads(check[0]): return True
    raise commands.MissingPermissions([perm])
   return commands.check(predicate)  

async def has_perms(ctx: commands.Context, perm: str=None): 
    if not perm: return True 
    if ctx.guild.owner == ctx.author or ctx.author.guild_permissions.administrator: return True
    for r in ctx.author.roles:
     if perm in [str(p[0]) for p in r.permissions if p[1] is True]: return True 
     check = await ctx.bot.db.fetchrow("SELECT permissions FROM fake_perms WHERE role_id = $1 and guild_id = $2", r.id, r.guild.id)
     if not check: continue 
     if perm in json.loads(check[0]) or "administrator" in json.loads(check[0]): return True
    return False

async def identify(self):
    payload = {
        'op': self.IDENTIFY,
        'd': {
            'token': self.token,
            'properties': {
                '$os': sys.platform,
                '$browser': 'Discord iOS',
                '$device': 'Discord iOS',
                '$referrer': '',
                '$referring_domain': ''
            },
            'compress': True,
            'large_threshold': 250,
            'v': 3
        }
    }

    if self.shard_id is not None and self.shard_count is not None:
        payload['d']['shard'] = [self.shard_id, self.shard_count]

    state = self._connection
    if state._activity is not None or state._status is not None:
        payload['d']['presence'] = {
            'status': state._status,
            'game': state._activity,
            'since': 0,
            'afk': False
        }

    if state._intents is not None:
        payload['d']['intents'] = state._intents.value

    await self.call_hooks('before_identify', self.shard_id, initial=self._initial_identify)
    await self.send_as_json(payload)

class VilanContext(commands.Context):
 def __init__(self, **kwargs):
  super().__init__(**kwargs)
 
 def find_role(self, name: str): 
   for role in self.guild.roles:
    if role.name == "@everyone": continue  
    if name.lower() in role.name.lower(): return role 
   return None
 
 async def send(self, *args, **kwargs):
  chec = await self.bot.db.fetchrow("SELECT * FROM reskin_toggle WHERE guild_id = $1", self.guild.id)
  if not chec: return await super().send(*args, **kwargs)
  check = await self.bot.db.fetchrow("SELECT * FROM reskin WHERE user_id = $1", self.author.id)
  if check:
    if kwargs.get('delete_after'):
      kwargs.pop('delete_after')
    if kwargs.get('reference'):
      kwargs.pop('reference')
    kwargs.update({'wait': True})
    kwargs['username'] = check['name']
    kwargs['avatar_url'] = check['avatar']
    webhooks = [w for w in await self.channel.webhooks() if w.user.id == self.guild.me.id]
    if len(webhooks) == 0: webhook = await self.channel.create_webhook(name="vilan - reskin")
    else: webhook = webhooks[0]
    return await webhook.send(*args, **kwargs)
  
  return await super().send(*args, **kwargs)
 
 async def reply(self, *args, **kwargs):
  return await self.send(*args, **kwargs)
 
 async def approve(self, message: str) -> discord.Message:
   return await self.reply(embed=discord.Embed(color=self.bot.color, description=f"{self.bot.yes} {self.author.mention}: {message}"))
 
 async def error(self, message: str) -> discord.Message:
   return await self.reply(embed=discord.Embed(color=self.bot.color, description=f"{self.bot.no} {self.author.mention}: {message}"))

 async def warn(self, message: str) -> discord.Message:
   return await self.reply(embed=discord.Embed(color=self.bot.color, description=f"{self.bot.warn} {self.author.mention}: {message}"))

 async def neutral(self, message: str, emoji: str="") -> discord.Message:
   return await self.reply(embed=discord.Embed(color=self.bot.color, description=f"{emoji} {self.author.mention}: {message}"))
 
 async def paginate(self, embeds: List[discord.Embed]):
  if len(embeds) == 1: return await self.send(embed=embeds[0])
  view = PgView(self, embeds)
  view.message = await self.reply(embed=embeds[0], view=view)

 async def cmdhelp(self): 
    command = self.command
    commandname = f"{str(command.parent)} {command.name}" if str(command.parent) != "None" else command.name
    if command.cog_name == "owner": return
    embed = discord.Embed(color=self.bot.color, title=commandname, description=command.description)
    embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar.url)
    if command.help is not None: embed.add_field(name="module", value=f"{command.help}")
    if command.brief is not None: embed.add_field(name="permissions", value=command.brief if command.brief else "any")
    embed.add_field(name="usage", value=f"```{commandname} {command.usage if command.usage else ''}```", inline=False)
    if len(command.aliases) > 0: embed.add_field(name="aliases", value=f"{','.join(map(str, command.aliases))}")
    await self.reply(embed=embed)

 async def create_pages(self): 
  embeds = []
  p=0
  for command in self.command.commands: 
    commandname = f"{str(command.parent)} {command.name}" if str(command.parent) != "None" else command.name
    p+=1 
    embed = discord.Embed(color=self.bot.color, title=f"{commandname}", description=command.description)
    embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.display_avatar.url)
    if command.help is not None: embed.add_field(name="module", value=f"{command.help}")
    if command.brief is not None: embed.add_field(name="permissions", value=command.brief if command.brief else "any")
    embed.add_field(name="usage", value=f"```{commandname} {command.usage if command.usage else ''}```", inline=False)
    if len(command.aliases) > 0: embed.add_field(name="aliases", value=f"{', '.join(a for a in command.aliases)}")
    embed.set_footer(text=f"page: {p}/{len(self.command.commands)}")
    embeds.append(embed)
     
  return await self.paginate(embeds)

class CustomInteraction(discord.Interaction):
 def __init__(self, **kwargs):
  super().__init__(**kwargs)
 
 async def approve(self, message: str, ephemeral: bool=True):
  return await self.response.send_message(embed=discord.Embed(color=self.client.color, description=f"{self.client.yes} {self.user.mention}: {message}"), ephemeral=ephemeral)
 
 async def error(self, message: str, ephemeral: bool=True):
  return await self.response.send_message(embed=discord.Embed(color=self.client.color, description=f"{self.client.no} {self.user.mention}: {message}"), ephemeral=ephemeral)

 async def warn(self, message: str, ephemeral: bool=True):
  return await self.response.send_message(embed=discord.Embed(color=self.client.color, description=f"{self.client.warn} {self.user.mention}: {message}"), ephemeral=ephemeral)

 async def neutral(self, message: str, emoji: str="", ephemeral: bool=True):
  return await self.response.send_message(embed=discord.Embed(color=self.client.color, description=f"{emoji} {self.user.mention}: {message}"), ephemeral=ephemeral)

class Custom:
  def __init__(self, bot: commands.AutoShardedBot):
    self.bot = bot
  
  def generate_key():
    return "".join(random.choice(string.ascii_letters + string.digits) for s in range(6))

  async def checkthekey(self):
    key: str
    check = await self.bot.db.fetchrow("SELECT * FROM cmderror WHERE code = $1", key)
    if check: 
      newkey = await generate_key(key)
      return await checkthekey(newkey)
    return key  

class ext(object):
  def __init__(self, bot: commands.AutoShardedBot):
    self.bot = bot
  
  async def approve(self, ctx: Union[commands.Context, discord.Interaction], message: str, ephemeral: bool=True) -> discord.Message or None: 
    if isinstance(ctx, commands.Context): return await ctx.reply(embed=discord.Embed(color=self.bot.color, description=f"{self.bot.yes} {ctx.author.mention}: {message}"))
    else: return await ctx.response.send_message(embed=discord.Embed(color=self.bot.color, description=f"{self.bot.yes} {ctx.user.mention}: {message}"), ephemeral=ephemeral)
  
  async def error(self, ctx: Union[commands.Context, discord.Interaction], message: str, ephemeral: bool=True) -> discord.Message or None: 
    if isinstance(ctx, commands.Context): return await ctx.reply(embed=discord.Embed(color=self.bot.color, description=f"{self.bot.no} {ctx.author.mention}: {message}"))
    else: return await ctx.response.send_message(embed=discord.Embed(color=self.bot.color, description=f"{self.bot.no} {ctx.user.mention}: {message}"), ephemeral=ephemeral)
  
  async def warn(self, ctx: Union[commands.Context, discord.Interaction], message: str, ephemeral: bool=True) -> discord.Message or None:
    if isinstance(ctx, commands.Context): return await ctx.reply(embed=discord.Embed(color=self.bot.color, description=f"{self.bot.warn} {ctx.author.mention}: {message}"))
    else: return await ctx.response.send_message(embed=discord.Embed(color=self.bot.color, description=f"{self.bot.warn} {ctx.user.mention}: {message}"), ephemeral=ephemeral)
  
  async def neutral(self, ctx: Union[commands.Context, discord.Interaction], message: str, emoji: str="", ephemeral: bool=True) -> discord.Message or None: 
    if isinstance(ctx, commands.Context): return await ctx.reply(embed=discord.Embed(color=self.bot.color, description=f"{emoji} {ctx.author.mention}: {message}"))
    else: return await ctx.response.send_message(embed=discord.Embed(color=self.bot.color, description=f"{emoji} {ctx.user.mention}: {message}"), ephemeral=ephemeral)
  
  def human_format(self, number) -> str:
    units = ['', 'K', 'M', 'G', 'T', 'P']
    if number < 1000:
      return number

    k = 1000.0
    magnitude = int(floor(log(number, k)))
    return '%.2f%s' % (number / k**magnitude, units[magnitude])
  
  def relative_time(self, date):
    """Take a datetime and return its "age" as a string.
    The age can be in second, minute, hour, day, month or year. Only the
    biggest unit is considered, e.g. if it's 2 days and 3 hours, "2 days" will
    be returned.
    Make sure date is not in the future, or else it won't work.
    """

    def formatn(n, s):
        """Add "s" if it's plural"""

        if n == 1:
            return "1 %s" % s
        elif n > 1:
            return "%d %ss" % (n, s)

    def qnr(a, b):
        """Return quotient and remaining"""

        return a / b, a % b

    class FormatDelta:

        def __init__(self, dt):
            now = datetime.datetime.now()
            delta = now - dt
            self.day = delta.days
            self.second = delta.seconds
            self.year, self.day = qnr(self.day, 365)
            self.month, self.day = qnr(self.day, 30)
            self.hour, self.second = qnr(self.second, 3600)
            self.minute, self.second = qnr(self.second, 60)

        def format(self):
            for period in ['year', 'month', 'day', 'hour', 'minute', 'second']:
                n = getattr(self, period)
                if n >= 1:
                    return '{0} ago'.format(formatn(n, period))
            return "just now"

    return FormatDelta(date).format()
  
  @property 
  def uptime(self) -> str:
    uptime = int(time.time() - self.bot.uptime)
    seconds_to_minute   = 60
    seconds_to_hour     = 60 * seconds_to_minute
    seconds_to_day      = 24 * seconds_to_hour
    days    =   uptime // seconds_to_day
    uptime    %=  seconds_to_day
    hours   =   uptime // seconds_to_hour
    uptime    %=  seconds_to_hour
    minutes =   uptime // seconds_to_minute
    uptime    %=  seconds_to_minute
    seconds = uptime
    if days > 0: return ("{} days, {} hours, {} minutes, {} seconds".format(days, hours, minutes, seconds))
    if hours > 0 and days == 0: return ("{} hours, {} minutes, {} seconds".format(hours, minutes, seconds))
    if minutes > 0 and hours == 0 and days == 0: return ("{} minutes, {} seconds".format(minutes, seconds))
    if minutes == 0 and hours == 0 and days == 0: return ("{} seconds".format(seconds))
    
class StartUp:
 async def loadcogs(self):
  for file in os.listdir("./cogs"):
   if file.endswith(".py"):
    try:
        await self.load_extension(f"cogs.{file[:-3]}")
        print(f"loaded module {file[:-3]}")
    except Exception as e: print("Unable to load module {} - {}".format(file[:-3], e))
  for fil in os.listdir("./events"):
   if fil.endswith(".py"):
    try:
        await self.load_extension(f"events.{fil[:-3]}")
        print(f"Loaded event {fil[:-3]}")
    except Exception as e: print("Unable to load event {} - {}".format(fil[:-3], e))

class Help(commands.HelpCommand):
  def __init__(self, **kwargs):
   super().__init__(**kwargs)
  
  async def send_bot_help(self, mapping):  
    embed = discord.Embed(color=self.context.bot.color, description="vilan is a multi-purpose bot with useful features").add_field(name="help", value="for command help use `;help [command]`\njoin the [**support server**](https://discord.gg/DX4MxrxsCg)").set_author(name=self.context.bot.user.name, icon_url=self.context.bot.user.avatar.url).set_footer(text=f"total commands {len(self.context.bot.commands)}")
    options = [
       discord.SelectOption(
         label="home",
         description="home page",
         emoji="<:beat_home:1135126792852742274>"
       ),
       discord.SelectOption(
         label="info",
         description="info commands",
         emoji="<:beat_info:1135123758173139044>"
       ),
       discord.SelectOption(
         label="moderation",
         description="moderation commands",
         emoji="<:beat_moderation:1135123727026245742>"
       ),
       discord.SelectOption(
         label="voicemaster",
         description="voicemaster commands",
         emoji="<:beat_voicemaster:1139625365761970337>"
       ),
       discord.SelectOption(
         label="antinuke",
         description="antinuke commands",
         emoji="<:beat_antinuke:1146368534360883300>"
       ),
       discord.SelectOption(
         label="config",
         description="config commands",
         emoji="<:beat_config:1135123657111384135>"
       ),
       discord.SelectOption(
         label="automod",
         description="automod commands",
         emoji="<:beat_automod:1143839715359989771>"
       ),
       discord.SelectOption(
         label="utility",
         description="utility commands",
         emoji="<:beat_utility:1135123776212832276>"
       ),
       discord.SelectOption(
         label="emoji",
         description="emoji commands",
         emoji="<:beat_emoji:1135123743396605962>"
       ),
       discord.SelectOption(
         label="lastfm",
         description="lastfm commands",
         emoji="<:lastfm:1138839782408060978>"
       ),
       discord.SelectOption(
         label="music",
         description="music commands",
         emoji="🎵"
       ),
       discord.SelectOption(
         label="economy",
         description="economy commands",
         emoji="💵"
       ),
       discord.SelectOption(
         label="fun",
         description="fun commands",
         emoji="🎮"
       ),
       discord.SelectOption(
         label="roleplay",
         description="roleplay commands",
         emoji="🎭"
       ),
       discord.SelectOption(
         label="donor",
         description="donor commands",
         emoji="🤑"
       )
    ]
    select = discord.ui.Select(options=options, placeholder="Select a category")

    async def select_callback(interaction: discord.Interaction): 
     if interaction.user.id != self.context.author.id: return await interaction.warn("You are not the author of this embed", ephemeral=True)
     if select.values[0] == "home": return await interaction.response.edit_message(embed=embed)
     com = []
     for c in [cm for cm in set(self.context.bot.walk_commands()) if cm.help == select.values[0]]:
      if c.parent: 
        if str(c.parent) in com: continue 
        com.append(str(c.parent))
      else: com.append(c.name)  
     e = discord.Embed(color=self.context.bot.color, description="```<> - optional | [] - required```\nfor command help use `;help [command]`\njoin the [**support server**](https://discord.gg/DX4MxrxsCg)").add_field(name="commands", value=f"```{', '.join(com)}```").set_author(name=self.context.bot.user.name, icon_url=self.context.bot.user.avatar.url) 
     return await interaction.response.edit_message(embed=e)
    select.callback = select_callback

    view = discord.ui.View(timeout=None)
    view.add_item(select) 
    return await self.context.reply(embed=embed, view=view)

  async def send_command_help(self, command: commands.Command): 
    commandname = f"{str(command.parent)} {command.name}" if str(command.parent) != "None" else command.name
    if command.cog_name == "owner": return
    embed = discord.Embed(color=self.context.bot.color, title=commandname, description=command.description)
    embed.set_author( name=self.context.bot.user.name, icon_url=self.context.bot.user.avatar.url)
    if command.help is not None: embed.add_field(name="module", value=f"{command.help}")
    if command.brief is not None: embed.add_field(name="permissions", value=command.brief if command.brief else "any")
    embed.add_field(name="usage", value=f"```{commandname} {command.usage if command.usage else ''}```", inline=False)
    if command.aliases is not None: embed.add_field(name="aliases", value=f"{', '.join(map(str, command.aliases))}")
    channel = self.get_destination()
    await channel.send(embed=embed)

  async def send_group_help(self, group: commands.Group): 
   ctx = self.context
   embeds = []
   p=0
   for command in group.commands: 
    commandname = f"{str(command.parent)} {command.name}" if str(command.parent) != "None" else command.name
    p+=1 
    embed = discord.Embed(color=ctx.bot.color, title=f"{commandname}", description=command.description)
    embed.set_author(name=ctx.bot.user.name, icon_url=ctx.bot.user.display_avatar.url)
    if command.help is not None: embed.add_field(name="module", value=f"{command.help}")
    if command.brief is not None: embed.add_field(name="permissions", value=command.brief if command.brief else "any")
    embed.add_field(name="usage", value=f"```{commandname} {command.usage if command.usage else ''}```", inline=False)
    if len(command.aliases) > 0: embed.add_field(name="aliases", value=f"{', '.join(a for a in command.aliases)}")
    embed.set_footer(text=f"page: {p}/{len(group.commands)}")
    embeds.append(embed)
     
   return await ctx.paginate(embeds) 