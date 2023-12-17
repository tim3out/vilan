import discord, datetime, humanfriendly
from discord.ext import commands
from tools.converters import NoStaff, GoodRole
from tools.predicates import server_owner, is_mod
from typing import Union
from tools.views import ClearMod
from tools.invoke import Invoke

class moderation(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
    
    @commands.command(description="disable the moderation features in your server", help="moderation")
    @commands.has_permissions("administrator")
    async def unsetmod(self, ctx: commands.Context): 
     check = await self.bot.db.fetchrow("SELECT * FROM mod WHERE guild_id = $1", ctx.guild.id)
     if not check: return await ctx.warn("Moderation is **not** enabled") 
     view = ClearMod(ctx)
     view.message = await ctx.reply(view=view, embed=discord.Embed(color=self.bot.color, description=f"{ctx.author.mention} Are you sure you want to disable moderation?")) 

    @commands.command(description="enable the moderation features in your server", help="moderation")
    @commands.has_permissions("administrator")
    async def setmod(self, ctx: commands.Context): 
     check = await self.bot.db.fetchrow("SELECT * FROM mod WHERE guild_id = $1", ctx.guild.id)
     if check: return await ctx.warn("Moderation is **already** enabled")
     await ctx.typing()
     role = await ctx.guild.create_role(name="vilan-jail")
     for channel in ctx.guild.channels: await channel.set_permissions(role, view_channel=False)
     overwrite = {role: discord.PermissionOverwrite(view_channel=True), ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False)}
     over = {ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False)}
     category = await ctx.guild.create_category(name="vilan mod", overwrites=over)
     text = await ctx.guild.create_text_channel(name="mod-logs", overwrites=over, category=category)
     jai = await ctx.guild.create_text_channel(name="jail", overwrites=overwrite, category=category)
     await self.bot.db.execute("INSERT INTO mod VALUES ($1,$2,$3,$4)", ctx.guild.id, text.id, jai.id, role.id)
     await self.bot.db.execute("INSERT INTO cases VALUES ($1,$2)", ctx.guild.id, 0)
     return await ctx.approve("Moderation has been enanled")
    
    @commands.command(description="ban a member from the server", usage="[member]", brief="ban members", help="moderation")
    @commands.has_permissions("ban_members")
    async def ban(self, ctx: commands.Context, member: NoStaff, *, reason:str="No reason provided"):
      await ctx.guild.ban(user=member, reason=reason + " | banned by {}".format(ctx.author))
      if not await Invoke.invoke_send(ctx, member, reason): await ctx.approve(f"**{member}** got banned")
    
    @commands.command(description="kick a member from the server", usage="[member]", brief="kick members", help="moderation")
    @commands.has_permissions("kick_members")
    async def kick(self, ctx: commands.Context, member: NoStaff, *, reason:str="No reason provided"):
      await ctx.guild.kick(user=member, reason=reason + " | kicked by {}".format(ctx.author))
      if not await Invoke.invoke_send(ctx, member, reason): await ctx.approve(f"**{member}** got kicked")
    
    @commands.command(description="unbans an user", usage="[user]", brief="ban members", help="moderation")
    @commands.has_permissions("ban_members")
    async def unban(self, ctx: commands.Context, member: discord.User, *, reason: str="No reason provided"):
      try:
       await ctx.guild.unban(member, reason=reason + " | unbanned by {}".format(ctx.author))
       if not await Invoke.invoke_send(ctx, member, reason): await ctx.approve(f"**{member}** has been unbanned")
      except discord.NotFound: return await ctx.warn(f"**{member}** is not banned")
    
    @commands.command(aliases=['p'], description="bulk delete messages", brief="manage messages", usage="[messages]", help="moderation")
    @commands.has_permissions("manage_messages")
    async def purge(self, ctx: commands.Context, amount: int, *, member: NoStaff=None):
     if not member: 
      return await ctx.channel.purge(limit=amount+1, bulk=True, reason=f"purge invoked by {ctx.author}")
     messages = []
     async for m in ctx.channel.history(): 
      if m.author.id == member.id: messages.append(m)
      if len(messages) == amount: break 
     messages.append(ctx.message)
     return await ctx.channel.delete_messages(messages)
  
    @commands.command(description="bulk delete messages sent by bots", usage="[amount]", aliases=["bc", "botclear"], help="moderation")
    @commands.has_permissions("manage_messages")
    async def botpurge(self, ctx: commands.Context):
      await ctx.channel.delete_messages([message async for message in ctx.channel.history() if message.author.bot])
    
    @commands.command(aliases=["setnick", "nick"], description="change an user's nickname", usage="[member] <nickname>", help="moderation")
    @commands.has_permissions("manage_nicknames")
    async def nickname(self, ctx, member: NoStaff, *, nick: str=None):
      if nick == None or nick.lower() == "none": return await ctx.approve(f"Removed **{member.name}'s** nickname")
      await member.edit(nick=nick)
      return await ctx.approve(f"Changed **{member.name}'s** nickname to **{nick}**")
    
    @commands.command(description="mute members in your server", brief="moderate members", usage="[member] [time] <reason>", aliases=["timeout"], help="moderation")
    @commands.has_permissions("moderate_members")
    async def mute(self, ctx: commands.Context, member: NoStaff, time: str="60s", *, reason="No reason provided"): 
     await member.timeout(discord.utils.utcnow() + datetime.timedelta(seconds=humanfriendly.parse_timespan(time)), reason=reason + " | {}".format(ctx.author))
     if not await Invoke.invoke_send(ctx, member, reason): await ctx.approve(f"**{member}** has been muted for {humanfriendly.format_timespan(humanfriendly.parse_timespan(time))} | {reason}")
    
    @commands.command(description="unmute a member in your server", brief="moderate members", usage="[member] <reason>", aliases=["untimeout"], help="moderation")
    @commands.has_permissions("moderate_members")
    async def unmute(self, ctx: commands.Context, member: NoStaff, * , reason: str="No reason provided"): 
      if not member.is_timed_out(): return await ctx.warn( f"**{member}** is not muted")
      await member.edit(timed_out_until=None, reason=reason + " | {}".format(ctx.author))
      if not await Invoke.invoke_send(ctx, member, reason): await ctx.approve(f"unmuted **{member}**")
    
    @commands.command(description="clone a channel", brief="server owner", help="moderation")
    @server_owner()
    async def nuke(self, ctx: commands.Context): 
     embed = discord.Embed(color=self.bot.color, description=f"Do you want to **nuke** this channel?")
     yes = discord.ui.Button(emoji=self.bot.yes)
     no = discord.ui.Button(emoji=self.bot.no)

     async def yes_callback(interaction: discord.Interaction): 
      if not interaction.user == ctx.guild.owner: return await interaction.warn("You are not the **author** of this embed")
      c = await interaction.channel.clone()
      await c.edit(position=ctx.channel.position)
      await ctx.channel.delete()
      await c.send(content="first g")
   
     async def no_callback(interaction: discord.Interaction): 
      if not interaction.user == ctx.guild.owner: return await interaction.warn("You are not the **author** of this embed")
      await interaction.response.edit_message(embed=discord.Embed(color=self.bot.color, description="aborting action..."), view=None)
   
     yes.callback = yes_callback
     no.callback = no_callback 
     view = discord.ui.View()
     view.add_item(yes)
     view.add_item(no)
     await ctx.reply(embed=embed, view=view)
    
    
    @commands.command(description="jail a member", usage="[member]", help="moderation", brief="manage channels")
    @commands.has_permissions("manage_channels")
    @is_mod()
    async def jail(self, ctx: commands.Context, member: NoStaff, *, reason: str="No reason provided"):
      check = await self.bot.db.fetchrow("SELECT * FROM jail WHERE guild_id = $1 AND user_id = $2", ctx.guild.id, member.id)      
      if check: return await ctx.warn(f"**{member}** is already jailed")
      roles = [r.id for r in member.roles if r.name != "@everyone" and r.is_assignable()]
      await self.bot.db.execute("INSERT INTO jail VALUES ($1,$2,$3)", ctx.guild.id, member.id, json.dumps(roles))   
      chec = await self.bot.db.fetchrow("SELECT * FROM mod WHERE guild_id = $1", ctx.guild.id)
      try:
       jail = ctx.guild.get_role(chec['role_id'])
       new = [r for r in member.roles if not r.is_assignable()]
       new.append(jail) 
       await member.edit(roles=new, reason=f"jailed by {ctx.author} - {reason}")
       if not await Invoke.invoke_send(ctx, member, reason): await ctx.approve(f"**{member}** got jailed - {reason}")
      except: return await ctx.error(f"There was a problem jailing **{member}**")

    @commands.command(description="unjail a member", usage="[member] [reason]", help="moderation", brief="manage channels")
    @commands.has_permissions("manage_channels")
    @is_mod()
    async def unjail(self, ctx: commands.Context, member: discord.Member, *, reason: str="No reason provided"):   
      check = await self.bot.db.fetchrow("SELECT * FROM jail WHERE guild_id = $1 AND user_id = $2", ctx.guild.id, member.id)      
      if not check: return await ctx.warn(f"**{member}** is not jailed")
      try: await member.edit(roles=[ctx.guild.get_role(role) for role in json.loads(check['roles']) if ctx.guild.get_role(role)], reason=f"unjailed by {ctx.author}")
      except: pass
      await self.bot.db.execute("DELETE FROM jail WHERE user_id = {} AND guild_id = {}".format(member.id, ctx.guild.id))
      if not await Invoke.invoke_send(ctx, member, reason): await ctx.approve(f"Unjailed **{member}**")
    
    @commands.command(aliases=["sm"], description="add slowmode to a channel", usage="[seconds] <channel>", help="moderation")
    @commands.has_permissions("manage_channels")
    async def slowmode(self, ctx: commands.Context, seconds: str, channel: discord.TextChannel=None):
      chan = channel or ctx.channel
      await chan.edit(slowmode_delay=humanfriendly.parse_timespan(seconds), reason="slowmode invoked by {}".format(ctx.author))
      return await ctx.approve(f"Slowmode set to **{humanfriendly.format_timespan(humanfriendly.parse_timespan(seconds))}** for {chan.mention}")

    @commands.command(description="lock a channel", usage="<channel>", help="moderation")
    @commands.has_permissions("manage_channels")
    async def lock(self, ctx: commands.Context, channel : discord.TextChannel=None):
      channel = channel or ctx.channel
      overwrite = channel.overwrites_for(ctx.guild.default_role)
      overwrite.send_messages = False
      await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
      return await ctx.approve(f"locked {channel.mention}")

    @commands.command(description="unlock a channel", usage="<channel>", help="moderation")
    @commands.has_permissions("manage_channels")
    async def unlock(self, ctx: commands.Context, channel : discord.TextChannel=None):
      channel = channel or ctx.channel
      overwrite = channel.overwrites_for(ctx.guild.default_role)
      overwrite.send_messages = True
      await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
      return await ctx.approve(f"unlocked {channel.mention}")       
    
    @commands.command(description="hide a channel", usage="<channel>", help="moderation")
    @commands.has_permissions("manage_channels")
    async def hide(self, ctx: commands.Context, channel : discord.TextChannel=None):
      channel = channel or ctx.channel
      overwrite = channel.overwrites_for(ctx.guild.default_role)
      overwrite.view_channel = False
      await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
      return await ctx.approve(f"hidden {channel.mention}")
    
    @commands.command(description="reveal a channel", usage="<channel>", help="moderation")
    @commands.has_permissions("manage_channels")
    async def reveal(self, ctx: commands.Context, channel : discord.TextChannel=None):
      channel = channel or ctx.channel
      overwrite = channel.overwrites_for(ctx.guild.default_role)
      overwrite.view_channel = True
      await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
      return await ctx.approve(f"revealed {channel.mention}")       
    
    @commands.group(invoke_without_command=True)
    async def role(self, ctx):
      await ctx.create_pages()
    
    @role.command(name="add", description="add a role to a member", usage="[member] [role]", help="moderation")
    @commands.has_permissions("manage_roles")
    async def role_add(self, ctx: commands.Context, user: discord.Member, *, role: GoodRole):
      if role in user.roles: return await ctx.error(f"**{user}** has this role already") 
      await user.add_roles(role)
      return await ctx.approve(f"Added {role.mention} to **{user.name}**")
   
    @role.command(name="remove", description="remove a role from a member", usage="[member] [role]", help="moderation")
    @commands.has_permissions("manage_roles")
    async def role_remove(self, ctx: commands.Context, user: discord.Member, *, role: GoodRole):
      if not role in user.roles: return await ctx.error(f"**{user}** doesn't have this role")
      await user.remove_roles(role)
      return await ctx.approve(f"Removed {role.mention} from **{user.name}**")   
    
    @role.command(name="create", description="create a role", usage="[name]", help="moderation")
    @commands.has_permissions("manage_roles")
    async def role_create(self, ctx: commands.Context, *, name: str):
        role = await ctx.guild.create_role(name=name, reason="Role created by {}".format(ctx.author))
        return await ctx.approve(f"Created role - {role}")
    
    @role.command(description="delete a role", usage="[role]", brief="manage roles", help="moderation")
    @commands.has_permissions("manage_roles")
    async def delete(self, ctx: commands.Context, *, role: GoodRole): 
      await role.delete()
      return await ctx.approve("Deleted the role") 
    
    @role.group(invoke_without_command=True, description="edit a role", help="moderation")
    async def edit(self, ctx: commands.Context): 
     return await ctx.create_pages()
   
    @edit.command(description="make a role visible separately or not", brief="manage roles", usage="[role] [true or false]", help="moderation")
    @commands.has_permissions("manage_roles")
    async def hoist(self, ctx: commands.Context, role: GoodRole, state: str): 
     if not state.lower() in ["true", "false"]: return await ctx.error(f"**{state}** can only be true or false")
     await role.edit(hoist=bool(state.lower() == "true"))
     return await ctx.approve(f"{f'The role is now hoisted' if role.hoist is True else 'The role is not hoisted anymore'}")

    @edit.command(aliases=["pos"], description="change a role's position", usage="[role] [position]", brief="manage roles", help="moderation")
    @commands.has_permissions("manage_roles")
    async def position(self, ctx: commands.Context, role: GoodRole, *, position: int):
     await role.edit(position=position)
     return await ctx.approve(f"Changed role position to `{position}`")
    
    @edit.command(brief="manage roles", description="change a role's name", usage="[role] [name]", help="moderation")
    @commands.has_permissions("manage_roles")
    async def name(self, ctx: commands.Context, role: GoodRole, *, name: str): 
     await role.edit(name=name, reason=f"role edited by {ctx.author}")
     return await ctx.approve(f"Role name changed to **{name}**")

    @edit.command(description="change a role's color", usage="[role] [color]", brief="manage_roles", help="moderation")
    @commands.has_permissions("manage_roles")
    async def color(self, ctx: commands.Context, role: GoodRole, *, color: str):  
      try: 
        color = color.replace("#", "")
        await role.edit(color=int(color, 16), reason=f"role edited by {ctx.author}")
        return await ctx.reply(embed=discord.Embed(color=role.color, description=f"{self.bot.yes} {ctx.author.mention}: Changed role's color"))
      except: return await ctx.error("Unable to change the role's color")  
    
    @edit.command(description="change a role's icon", brief="manage roles", usage="[role] <emoji>", help="moderation")
    @commands.has_permissions("manage_roles")
    async def icon(self, ctx: commands.Context, role: GoodRole, emoji: Union[discord.PartialEmoji, str]):      
      if isinstance(emoji, discord.PartialEmoji): 
       by = await emoji.read()
       await role.edit(display_icon=by) 
      elif isinstance(emoji, str): await role.edit(display_icon=str(emoji))
      return await ctx.approve("Changed role icon")
    
    @role.group(invoke_without_command=True, name="humans", description="mass add or remove roles from members", help="moderation")
    async def rolehumans(self, ctx: commands.Context):
      return await ctx.create_pages()
  
    @rolehumans.command(name="remove", description="remove a role from all members in this server", usage='[role]', brief="manage_roles", help="moderation")
    @commands.has_permissions("manage_roles")
    async def rolehumansremove(self, ctx: commands.Context, *, role: GoodRole):
      message = await ctx.neutral(f"Removing {role.mention} to all humans...")
      try:
         for member in [m for m in ctx.guild.members if not m.bot]: 
            if not role in member.roles: continue
            await member.remove_roles(role)

         await message.edit(embed=discord.Embed(color=self.bot.color, description=f"{self.bot.yes} {ctx.author.mention}: Removed {role.mention} from all humans"))
      except Exception: await message.edit(embed=discord.Embed(color=self.bot.color, description=f"{self.bot.no} {ctx.author.mention}: Unable to remove {role.mention} from all humans"))  
  
    @rolehumans.command(name="add", description="add a role to all humans in this server", usage='[role]', brief="manage_roles", help="moderation")
    @commands.has_permissions("manage_roles")
    async def rolehumansadd(self, ctx: commands.Context, *, role: GoodRole):  
      message = await ctx.neutral(f"Adding {role.mention} to all humans...")
      try:
       for member in [m for m in ctx.guild.members if not m.bot]: 
         if role in member.roles: continue
         await member.add_roles(role)

       await message.edit(embed=discord.Embed(color=self.bot.color, description=f"{self.bot.yes} {ctx.author.mention}: Added {role.mention} to all humans"))
      except Exception: await message.edit(embed=discord.Embed(color=self.bot.color, description=f"{self.bot.no} {ctx.author.mention}: Unable to add {role.mention} to all humans")) 
    
    @role.group(invoke_without_command=True, name="all", description="mass add or remove roles from members", help="moderation")
    async def roleall(self, ctx: commands.Context):
      return await ctx.create_pages()
  
    @roleall.command(name="remove", description="remove a role from all members in this server", usage='[role]', brief="manage_roles", help="moderation")
    @commands.has_permissions("manage_roles")
    async def roleallremove(self, ctx: commands.Context, *, role: GoodRole):
      message = await ctx.neutral(f"Removing {role.mention} from all members")
      try:
         for member in ctx.guild.members: 
            if not role in member.roles: continue
            await member.remove_roles(role)

         await message.edit(embed=discord.Embed(color=self.bot.color, description=f"{self.bot.yes} {ctx.author.mention}: Removed {role.mention} from all members"))
      except Exception: await message.edit(embed=discord.Embed(color=self.bot.color, description=f"{self.bot.no} {ctx.author.mention}: Unable to remove {role.mention} from all members"))  
  
    @roleall.command(name="add", description="add a role to all members in this server", usage='[role]', brief="manage_roles", help="moderation")
    @commands.has_permissions("manage_roles")
    async def rolealladd(self, ctx: commands.Context, *, role: GoodRole):  
      message = await ctx.neutral(f"Adding {role.mention} to all members")
      try:
       for member in ctx.guild.members: 
         if role in member.roles: continue
         await member.add_roles(role)

       await message.edit(embed=discord.Embed(color=self.bot.color, description=f"{self.bot.yes} {ctx.author.mention}: Added {role.mention} to all members"))
      except Exception: await message.edit(embed=discord.Embed(color=self.bot.color, description=f"{self.bot.no} {ctx.author.mention}: Unable to add {role.mention} to all members"))
    
async def setup(bot):
    await bot.add_cog(moderation(bot))