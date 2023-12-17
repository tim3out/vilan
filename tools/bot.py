import os, dotenv, io, discord, time
from typing import Union, Optional, Any, List
from discord import (
    Intents,
    AllowedMentions,
    Interaction,
    Message
    )
from asyncpg import create_pool
from .helpers import identify, StartUp, VilanContext, CustomInteraction, Custom, Help, ext, perms, getprefix
from .session import Session
from cogs.music import music
from .views import vmbuttons, CreateTicket, DeleteTicket
from discord.gateway import DiscordWebSocket
from discord.ext import commands
from discord.ext.commands import (
    AutoShardedBot as AB,
    CommandError,
    NotOwner,
    MissingPermissions,
    MissingRequiredArgument,
    CooldownMapping,
    BucketType,
    CommandNotFound,
    BadArgument
    )

dotenv.load_dotenv(verbose=True)
DiscordWebSocket.identify = identify
os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"
os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_RETAIN"] = "True"
os.environ["JISHAKU_FORCE_PAGINATOR"] = "True"
Interaction.approve = CustomInteraction.approve
Interaction.wrong = CustomInteraction.error
Interaction.warn = CustomInteraction.warn
Interaction.neutral = CustomInteraction.neutral
commands.has_permissions = perms

class vilan(AB):
  def __init__(self):
   super().__init__(
    command_prefix=getprefix,
    intents=Intents.all(),
    help_command=Help(),
    allowed_mentions=AllowedMentions(roles=False, everyone=False, replied_user=False),
    case_sensitive=True,
    strip_after_prefix=True,
    owner_ids=[1074668481867419758],
   )
   self.uptime = time.time()
   self.pretend_api = "VYW49S8DCIZEE3CG"
   self.color = 0xa5e9ff
   self.yes = "<:check:1146359972444254248>"
   self.no = "<:stop:1146359810351169609>"
   self.warn = "<:warning:1133468940287352952>"
   self.proxy_url = "http://bdwlgfiq-rotate:ynr7of5herb6@p.webshare.io:80/"
   self.m_cd=CooldownMapping.from_cooldown(1,5,BucketType.member)
   self.c_cd=CooldownMapping.from_cooldown(1,5,BucketType.channel)
   self.m_cd2=CooldownMapping.from_cooldown(1,10,BucketType.member)
   self.global_cd = CooldownMapping.from_cooldown(2, 3, BucketType.member)
   self.ext = ext(self)
   self.main_guilds = [1132991358022467634]
   self.random_token = ""
  async def create_db_pool(self):
    self.db = await create_pool(port=5432, host=os.environ["pghost"], password=os.environ["pgpass"], database=os.environ["pgdb"], user=os.environ["pguser"])
  
  def __repr__(self):
    unchunked = len([guild for guild in self.guilds if not guild.chunked])
    return f"<vilan PID={os.getpid()}, unchunked_guilds={unchunked}>"
  
  async def get_context(self, message, *, cls=VilanContext):
    return await super().get_context(message, cls=cls)
  
  async def setup_hook(self) -> None:
    print("Hey g")
    self.session = Session()
    await self.load_extension("jishaku")
    self.loop.create_task(self.create_db_pool())
    self.add_view(CreateTicket())
    self.add_view(DeleteTicket())
    self.add_view(vmbuttons())
  
  def is_dangerous(self, role: discord.Role) -> bool:
     permissions = role.permissions
     return any([
      permissions.kick_members, permissions.ban_members,
      permissions.administrator, permissions.manage_channels,
      permissions.manage_guild, permissions.manage_messages,
      permissions.manage_roles, permissions.manage_webhooks,
      permissions.manage_emojis_and_stickers, permissions.manage_threads,
      permissions.mention_everyone, permissions.moderate_members
     ])
  
  async def gbytes(self, file: str): 
      return io.BytesIO(await self.session.read(file, proxy=self.proxy_url, ssl=False)) 
  
  async def prefixes(self, message: discord.Message) -> List[str]:
     prefixes = []
     for l in set(p for p in await self.command_prefix(self, message)): prefixes.append(l)
     return prefixes
  
  async def guild_change(self, mes: str, guild: discord.Guild) -> discord.Message:
     channel = self.get_channel(1138899089434619974)
     try: await channel.send(embed=discord.Embed(color=self.color, description=f"{mes} **{guild.name}** owned by **{guild.owner}** with **{guild.member_count}** members"))
     except: pass

  async def on_guild_join(self, guild: discord.Guild):
    if not guild.chunked: await guild.chunk(cache=True)
    await self.guild_change("joined", guild)

  async def on_guild_remove(self, guild: discord.Guild):
     await self.guild_change("left", guild)
  
  async def channel_rl(self,message:Message) -> Optional[int]:
        return self.c_cd.get_bucket(message).update_rate_limit()

  async def member_rl(self,message:Message) -> Optional[int]:
        return self.m_cd.get_bucket(message).update_rate_limit()
  
  async def on_ready(self):
    await music(self).start_nodes()
    await StartUp.loadcogs(self)
    print(f"Connected in as {self.user} {self.user.id}")
  
  async def on_message_edit(self, before, after):
    if before.content != after.content: await self.process_commands(after)
  
  async def on_message(self, message: Message): 
    channel_rl=await self.channel_rl(message)
    member_rl=await self.member_rl(message)
    if channel_rl == True: return
    if member_rl == True: return
    if message.content == "<@{}>".format(self.user.id): return await message.reply(embed=discord.Embed(color=self.color, description="prefix: " + ", ".join(f"`{g}`" for g in await self.prefixes(message))))
    await self.process_commands(message)

  async def on_command_error(self, ctx: commands.Context, error: CommandError):
      if isinstance(error, CommandNotFound): return
      elif isinstance(error, NotOwner): pass
      elif isinstance(error, commands.CheckFailure): 
        if isinstance(error, commands.MissingPermissions): return await ctx.warn(f"You are missing `{error.missing_permissions[0]}` permissions")
      elif isinstance(error, commands.CommandOnCooldown): 
        if ctx.command.name != "hit": return
      elif isinstance(error, MissingRequiredArgument): return await ctx.cmdhelp()
      elif isinstance(error, commands.EmojiNotFound): return await ctx.warn(f"Unable to convert {error.argument} into an **emoji**")
      elif isinstance(error, commands.MemberNotFound): return await ctx.warn(f"Unable to find member **{error.argument}**")
      elif isinstance(error, commands.UserNotFound): return await ctx.warn(f"Unable to find user **{error.argument}**")
      elif isinstance(error, commands.RoleNotFound): return await ctx.warn(f"Couldn't find role **{error.argument}**")
      elif isinstance(error, commands.ChannelNotFound): return await ctx.warn(f"Couldn't find channel **{error.argument}**")
      elif isinstance(error, commands.UserConverter): return await ctx.warn(f"Couldn't convert that into an **user** ")
      elif isinstance(error, commands.MemberConverter): return await ctx.warn("Couldn't convert that into a **member**")
      elif isinstance(error, BadArgument): return await ctx.warn(error.args[0])
      elif isinstance(error, commands.BotMissingPermissions): return await ctx.warn("I do not have enough **permission** to do this")
      elif isinstance(error, discord.HTTPException): return await ctx.warn("Unable to execute this command") 
      else: 
        key = Custom.generate_key()
        rl=await self.member_rl(ctx.message)
        if rl == True: return
        await self.db.execute("INSERT INTO cmderror VALUES ($1,$2)", key, str(error))
        await self.ext.warn(ctx, f"An unexpected error was found while running the command **{ctx.command.qualified_name}**. Please report the code `{key}` in our [**support server**](https://discord.gg/DX4MxrxsCg)")