import discord, json
from discord.ext import commands
from tools.embed import EmbedScript, EmbedBuilder
from tools.modals import br
from tools.predicates import has_booster_role, server_owner
from typing import Union
from tools.invoke import Invoke

class config(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
    
    @commands.command(description="create an embed using the embed parser", usage="[code]", aliases=["ce"], help="config")
    async def createembed(self, ctx: commands.Context, *, code: EmbedScript):
     await ctx.send(**code)
  
    @commands.command(help="config", description="shows variables for the embed")
    async def variables(self, ctx: commands.Context): 
     embed1 = discord.Embed(color=self.bot.color, title="user variables")
     embed1.description = """
     {user} - returns user full name
{user.name} - returns user's username
{user.mention} - mentions user
{user.joined_at} - returns the relative date the user joined the server
{user.created_at} - returns the relative time the user created the account
{user.discriminator} - returns the user discriminator
    """

     embed2 = discord.Embed(color=self.bot.color, title="guild variables")
     embed2.description = """
     {guild.name} - returns the server's name
{guild.count} - returns the server's member count
{guild.icon} - returns the server's icon
{guild.id} - returns the server's id 
{guild.boost_count} - returns the number of server's boosts
{guild.booster_count} - returns the number of boosters
{guild.boost_tier} - returns the server's boost level
{guild.vanity} - returns the guild vanity, if any
   """
     
     embed3 = discord.Embed(color=self.bot.color, title="invoke message variables")
     embed3.description = """
     {member} - returns member's name and discriminator
{member.name} - returns member's name
{member.mention} - returns member mention
{member.id} - return member's id
{member.avatar} - returns member's avatar
{reason} - returns action reason, if any
    """

     embed4 = discord.Embed(color=self.bot.color, title="last.fm variables")
     embed4.description = """
     {scrobbles} - returns all song play count
{trackplays} - returns the track total plays
{artistplays} - returns the artist total plays
{albumplays} - returns the album total plays
{track} - returns the track name
{trackurl} - returns the track url
{trackimage} - returns the track image
{artist} - returns the artist name
{artisturl} - returns the artist profile url
{album} - returns the album name 
{albumurl} - returns the album url
{username} - returns your username
{useravatar} - returns user's profile picture
    """
     
     await ctx.paginate([embed1, embed2, embed3, embed4])
    
    @commands.group(aliases=["ar"], invoke_without_command=True)
    async def autoresponder(self, ctx): 
      await ctx.create_pages()

    @autoresponder.command(name="add", description="add an autoresponder", usage="[trigger], [response]", help="config") 
    @commands.has_permissions("manage_guild")
    async def ar_add(self, ctx: commands.Context, *, arg: str): 
     arg = arg.split(', ')
     trigger = arg[0]
     try: response = arg[1]
     except: return await ctx.warn("No response found")
     check = await self.bot.db.fetchrow("SELECT * FROM autoresponder WHERE guild_id = $1 AND trigger = $2", ctx.guild.id, trigger)
     if check: 
      await self.bot.db.execute("UPDATE autoresponder SET response = $1 WHERE guild_id = $2 AND trigger = $3", response, ctx.guild.id, trigger)
      return await ctx.approve("Set response `{}` for the trigger `{}`".format(response, trigger))
     else: 
      await self.bot.db.execute("INSERT INTO autoresponder VALUES ($1,$2,$3)", ctx.guild.id, trigger, response)
      return await ctx.approve("Added autoresponder with trigger `{}` and response `{}`".format(trigger, response)) 

    @autoresponder.command(name="remove", description="remove an autoresponder", usage="[trigger], [response]", help="config")
    @commands.has_permissions("manage_guild")
    async def ar_remove(self, ctx: commands.Context, *, trigger: str): 
      check = await self.bot.db.fetchrow("SELECT * FROM autoresponder WHERE guild_id = $1 AND trigger = $2", ctx.guild.id, trigger)
      if not check: return await ctx.warn(f"Cannot find an autoresponder with the trigger `{trigger}`") 
      await self.bot.db.execute('DELETE FROM autoresponder WHERE guild_id = $1 AND trigger = $2', ctx.guild.id, trigger)
      await ctx.approve(f"Deleted autoresponder for the trigger `{trigger}`")
    
    @autoresponder.command(name="variables", description="returns variables for autoresponder", help="config")
    async def ar_variables(self, ctx: commands.Context): 
      await ctx.invoke(self.bot.get_command('embed variables'))
    
    @autoresponder.command(name="list", description="returns a list of all autoresponders", help="config")
    async def ar_list(self, ctx: commands.Context): 
     results = await self.bot.db.fetch("SELECT * FROM autoresponder WHERE guild_id = $1", ctx.guild.id)
     if len(results) == 0: return await ctx.warn("There are no **autoresponders**") 
     l=0
     k=0
     mes=""
     embeds = [] 
     for result in results: 
      k+=1 
      l+=1 
      mes=mes+f"`{k}` {result['trigger']} - {result['response']}\n"
      if l == 10: 
        embeds.append(discord.Embed(color=self.bot.color, title=f"autoresponders ({len(results)})", description=mes))
        l=0
     embeds.append(discord.Embed(color=self.bot.color, title=f"autoresponders ({len(results)})", description=mes)) 
     await ctx.paginate(embeds)
    
    @commands.group(invoke_without_command=True)
    async def autoreact(self, ctx): 
      await ctx.create_pages()

    @autoreact.command(name="add", description="make the bot react with emojis on your message", brief="manage guild", usage="[content], [emojis]", help="config")
    @commands.has_permissions("manage_guild")
    async def autoreact_add(self, ctx: commands.Context, *, content: str):
     con = content.split(",")
     if len(con) == 1: return await self.bot.help_command.send_command_help(ctx.command)
     emojis = [e for e in con[1].split(" ") if e != " "] 
     if len(emojis) == 0: return await self.bot.help_command.send_command_help(ctx.command)
     sql_as_text = json.dumps(emojis)  
     check = await self.bot.db.fetchrow("SELECT * FROM autoreact WHERE guild_id = $1 AND trigger = $2", ctx.guild.id, con[0])
     if check: await self.bot.db.execute("UPDATE autoreact SET emojis = $1 WHERE guild_id = $2 AND trigger = $3", sql_as_text, ctx.guild.id, con[0])   
     else: await self.bot.db.execute("INSERT INTO autoreact VALUES ($1,$2,$3)", ctx.guild.id, con[0], sql_as_text)
     await ctx.approve(f"Added autoreact for **{con[0]}** - {''.join([e for e in emojis])}")
  
    @autoreact.command(name="remove", description="remove auto reactions from a content", brief="manage guild", usage='[content]', help="config")
    @commands.has_permissions("manage_guild")
    async def autoreact_remove(self, ctx: commands.Context, *, content: str): 
     check = await self.bot.db.fetchrow("SELECT * FROM autoreact WHERE guild_id = $1 AND trigger = $2", ctx.guild.id, content)
     if not check: return await ctx.warn(f"No autoreact found for the trigger **{content}**")
     await self.bot.db.execute("DELETE FROM autoreact WHERE guild_id = $1 AND trigger = $2", ctx.guild.id, content)
     return await ctx.approve(f"Autoreact deleted for **{content}**")

    @autoreact.command(name="list", description="return a list of autoreactions in this server", help="config")
    async def autoreact_list(self, ctx: commands.Context): 
      check = await self.bot.db.fetch("SELECT * FROM autoreact WHERE guild_id = $1", ctx.guild.id)  
      if len(check) == 0: return await ctx.warn("this server has no **autoreactions**".capitalize())
      i=0
      k=1
      l=0
      mes = ""
      number = []
      messages = []
      for result in check:
              lol = json.loads(result['emojis'])
              mes = f"{mes}`{k}` {result['trigger']} - {''.join(l for l in lol)}\n"
              k+=1
              l+=1
              if l == 10:
               messages.append(mes)
               number.append(discord.Embed(color=self.bot.color, title=f"autoreactions ({len(check)})", description=messages[i]))
               i+=1
               mes = ""
               l=0
    
      messages.append(mes)
      embed = discord.Embed(color=self.bot.color, title=f"autoreactions ({len(check)})", description=messages[i])
      number.append(embed)
      await ctx.paginate(number)
    
    @commands.group(aliases=["br"], invoke_without_command=True)
    async def boosterrole(self, ctx):
      await ctx.create_pages()
    
    @boosterrole.command(name="setup", description="set the boosterrole module", help="config")
    @commands.has_permissions("manage_guild")
    async def br_setup(self, ctx: commands.Context):
        check = await self.bot.db.fetchrow("SELECT * FROM booster_module WHERE guild_id = $1", ctx.guild.id)
        if check: return await ctx.warn("Booster role module is **already** configured")
        else: await self.bot.db.execute("INSERT INTO booster_module (guild_id) VALUES ($1)", ctx.guild.id)
        return await ctx.approve("Configured booster role module")
    
    @boosterrole.command(description="unset the boosterrole module", help="config")
    @commands.has_permissions("manage_guild")
    async def br_remove(self, ctx: commands.Context): 
        check = await self.bot.db.fetchrow("SELECT * FROM booster_module WHERE guild_id = {}".format(ctx.guild.id))        
        if not check: return await ctx.warn("booster role module is **not** configured".capitalize())
        embed = discord.Embed(color=self.bot.color, description="Are you sure you want to remove the boosterrole module? This action cannot be **undone**")
        yes = discord.ui.Button(emoji=self.bot.yes)
        no = discord.ui.Button(emoji=self.bot.no)
        async def yes_callback(interaction: discord.Interaction):
          if interaction.user != ctx.author: return await interaction.warn("You are not the author of this embed")
          await self.bot.db.execute("DELETE FROM booster_module WHERE guild_id = $1", ctx.guild.id)
          await self.bot.db.execute("DELETE FROM booster_roles WHERE guild_id = $1", ctx.guild.id)        
          return await interaction.response.edit_message(embed=discord.Embed(color=self.bot.color, description=f"{self.bot.yes} {ctx.author.mention}: Booster role module has been cleared"), view=None)

        async def no_callback(interaction: discord.Interaction): 
          if interaction.user != ctx.author: return await interaction.warn("You are not the author of this embed")
          return await interaction.response.edit_message(embed=discord.Embed(color=self.bot.color, description="aborting action..."), view=None)

        yes.callback = yes_callback
        no.callback = no_callback
        view = discord.ui.View() 
        view.add_item(yes)
        view.add_item(no)
        await ctx.reply(embed=embed, view=view, mention_author=False) 
    
    @boosterrole.command(description="set a base role for boosterrole module", help="config")
    @commands.has_permissions("manage_guild")
    async def base(self, ctx: commands.Context, *, role: discord.Role=None):
      check = await self.bot.db.fetchrow("SELECT base FROM booster_module WHERE guild_id = {}".format(ctx.guild.id))      
      if not role:
        if not check: return await ctx.warn("Booster role module **base role** is not configured") 
        await self.bot.db.execute("UPDATE booster_module SET base = $1 WHERE guild_id = $2", None, ctx.guild.id) 
        return await ctx.approve("Base role has been removed")
      if role.position >= ctx.guild.get_member(self.bot.user.id).top_role.position: return await ctx.warn("This role cannot be a booster role base")
      await self.bot.db.execute("UPDATE booster_module SET base = $1 WHERE guild_id = $2", role.id, ctx.guild.id) 
      return await ctx.approve(f"set {role.mention} as base role".capitalize())
    
    @boosterrole.command(description="create a booster role", usage="<name>", help="config")
    async def create(self, ctx: commands.Context, name: str=None): 
      if not ctx.author in ctx.guild.premium_subscribers: return await ctx.warn("You are **not** a booster")
      che = await self.bot.db.fetchrow("SELECT * FROM booster_module WHERE guild_id = {}".format(ctx.guild.id))
      if not che: return await ctx.warn("Booster role module is **not** configured")
      check = await self.bot.db.fetchrow("SELECT * FROM booster_roles WHERE guild_id = {} AND user_id = {}".format(ctx.guild.id, ctx.author.id))
      if check: return await ctx.warn(f"You already have a booster role. Use `{ctx.clean_prefix}boosterrole edit` command for more")
      ro = ctx.guild.get_role(che['base'])
      role = await ctx.guild.create_role(name=f"{ctx.author.name}'s role" if not name else name)  
      await role.edit(position=ro.position if ro is not None else 1)
      await ctx.author.add_roles(role)
      await self.bot.db.execute("INSERT INTO booster_roles VALUES ($1,$2,$3)", ctx.guild.id, ctx.author.id, role.id)
      await ctx.invoke(self.bot.get_command('boosterrole edit'))
    
    @boosterrole.command(description="edit the booster role name", usage="[name]", help="config")
    @has_booster_role()
    async def name(self, ctx: commands.Context, *, name: str): 
      check = await self.bot.db.fetchrow("SELECT * FROM booster_roles WHERE guild_id = {} AND user_id = {}".format(ctx.guild.id, ctx.author.id))
      role = ctx.guild.get_role(check['role_id'])
      await role.edit(name=name)
      await ctx.approve(f"Booster role name changed to **{name}**")
    
    @boosterrole.command(description="edit the role icon", usage="[emoji]", help="config")
    @has_booster_role()
    async def icon(self, ctx: commands.Context, *, emoji: Union[discord.PartialEmoji, str]):      
      check = await self.bot.db.fetchrow("SELECT * FROM booster_roles WHERE guild_id = {} AND user_id = {}".format(ctx.guild.id, ctx.author.id))
      role = ctx.guild.get_role(check['role_id'])
      if isinstance(emoji, discord.PartialEmoji): icon = await self.bot.session.read(emoji.url)
      elif isinstance(emoji, str): icon = emoji  
      try:
       await role.edit(display_icon=icon)
       await ctx.approve(f"Changed your **booster role** icon")
      except discord.Forbidden as e: return await ctx.error(str(e))
    
    @boosterrole.command(description="change the booster role color", usage="[color]", help="config")
    @has_booster_role()
    async def color(self, ctx: commands.Context, color: str): 
     check = await self.bot.db.fetchrow("SELECT * FROM booster_roles WHERE guild_id = {} AND user_id = {}".format(ctx.guild.id, ctx.author.id))
     role = ctx.guild.get_role(check['role_id']) 
     color = color.replace("#", "")
     color = int(color, 16)
     await role.edit(color=color)
     return await ctx.approve(f"Changed your **booster role** color") 
    
    @boosterrole.command(description="edit the role hoist", help="config")
    @has_booster_role()
    async def hoist(self, ctx: commands.Context): 
     check = await self.bot.db.fetchrow("SELECT * FROM booster_roles WHERE guild_id = {} AND user_id = {}".format(ctx.guild.id, ctx.author.id))
     role = ctx.guild.get_role(check['role_id']) 
     await role.edit(hoist=False if role.hoist else True)
     return await ctx.approve("Changed your **booster role** hoist status")
    
    @boosterrole.command(description="chnage the role position", usage="[position]", aliases=["pos"], help="config")
    @has_booster_role()
    async def position(self, ctx: commands.Context, *, pos: int=1):
        check = await self.bot.db.fetchrow("SELECT * FROM booster_roles WHERE guild_id = $1 AND user_id = $2", ctx.guild.id, ctx.author.id)
        if not check: return await ctx.warn("You do not have a **booster role** created. Use `boosterrole create` to create one")
        role = ctx.guild.get_role(check["role_id"])
        if role.position >= ctx.guild.get_member(self.bot.user.id).top_role.position: return await ctx.warn("This role cannot be managed by the bot")
        if pos == 0: return await ctx.warn("Position cannot be lower than 1")
        await role.edit(position=pos)
        return await ctx.approve("Changed your **booster role** position to **{}**".format(pos))
    
    @boosterrole.command(description="delete the booster role", help="config")
    @has_booster_role()
    async def delete(self, ctx: commands.Context): 
      check = await self.bot.db.fetchrow("SELECT * FROM booster_roles WHERE guild_id = {} AND user_id = {}".format(ctx.guild.id, ctx.author.id))
      role = ctx.guild.get_role(check['role_id'])  
      await role.delete()
      await ctx.approve("Your **booster role** has been deleted")
    
    @boosterrole.command(description="edit a booster role", help="config")
    async def edit(self, ctx: commands.Context): 
        che = await self.bot.db.fetchrow("SELECT * FROM booster_module WHERE guild_id = {}".format(ctx.guild.id))
        if not che: return await ctx.warn("Booster role module is **not** configured")
        check = await self.bot.db.fetchrow("SELECT * FROM booster_roles WHERE guild_id = {} AND user_id = {}".format(ctx.guild.id, ctx.author.id))
        if not check: return await ctx.invoke(self.bot.get_command('boosterrole create'))         
        role = ctx.guild.get_role(check['role_id'])
        if not role: options = [
            discord.SelectOption( 
            label="delete",
            description="delete your booster role",
            emoji="<:trash:1145199851613720587>"
          ),
            discord.SelectOption(
            label="cancel",
            description="cancel the booster role edit",
            emoji=self.bot.no
            )]
        else: 
          options = [ 
          discord.SelectOption(
            label="name",
            description="change the booster role name",
            emoji="<:channel:1145188250273726464>"
          ),
          discord.SelectOption(
            label="color",
            description="change the color of your role",
            emoji="<:star:1133831173982924860>"
          ),
          discord.SelectOption(
            label="icon",
            description="change the icon",
            emoji="<:man:1145241989957296159>"
          ), 
          discord.SelectOption(
            label="hoist",
            description="make your role to be hoisted or not",
            emoji="<:unghost:1145193149044621342>"
          ),
          discord.SelectOption(
            label="position",
            description="change your role position",
            emoji="<:hammer:1145199036425584701>"
          ),
          discord.SelectOption( 
            label="delete",
            description="delete your booster role",
            emoji="<:trash:1145199851613720587>"
          ),
            discord.SelectOption(
            label="cancel",
            description="cancel the booster role edit",
            emoji=self.bot.no
          )
        ]
        embed = discord.Embed(color=self.bot.color, title="booster role edit menu", description="customize your custom role with the options from the dropdown menu below") 
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        select = discord.ui.Select(placeholder="select carefully", options=options)

        async def select_callback(interaction: discord.Interaction): 
          if ctx.author != interaction.user: return await interaction.warn("You are not the author of this embed")
          if select.values[0] == "cancel": return await interaction.response.edit_message(view=None)
          elif select.values[0] == "hoist": 
            await role.edit(hoist=False if role.hoist else True)
            return await interaction.approve("Changed your **booster role** hoist status")
          elif select.values[0] == "delete": 
             if role: await role.delete() 
             await self.bot.db.execute("DELETE FROM booster_roles WHERE guild_id = {} AND user_id = {}".format(interaction.guild.id, interaction.user.id)) 
             await interaction.approve("Your booster role has been deleted")
             return await interaction.message.delete()
          elif select.values[0] == "name":
            mod = br.Name()
            await interaction.response.send_modal(mod)    
          elif select.values[0] == "color":
            mod = br.Color()
            await interaction.response.send_modal(mod)
          elif select.values[0] == "icon":
            mod = br.Icon()
            await interaction.response.send_modal(mod)
          elif select.values[0] == "position":
            mod = br.Position()
            await interaction.response.send_modal(mod)

        select.callback = select_callback
        view = discord.ui.View()
        view.add_item(select)
        await ctx.reply(embed=embed, view=view)
    
    @commands.group(invoke_without_command=True)
    async def autorole(self, ctx): 
      await ctx.create_pages()

    @autorole.command(name="add", description="give a role to new users that joins your server", usage="[role]", brief="manage_guild", help="config")
    @commands.has_permissions("manage_guild")
    async def autorole_add(self, ctx: commands.Context, *, role: Union[discord.Role, str]):
      if isinstance(role, str):
        role = ctx.find_role(role)
        if not role: return await ctx.error(f"No role named **{ctx.message.clean_content[-len(ctx.clean_prefix)+15:]}** found")
      check = await self.bot.db.fetchrow("SELECT * FROM autorole WHERE guild_id = {} AND role_id = {}".format(ctx.guild.id, role.id))
      if check: return await ctx.error(f"{role.mention} is already added")
      await self.bot.db.execute("INSERT INTO autorole VALUES ($1,$2)", role.id, ctx.guild.id)
      return await ctx.approve(f"Added {role.mention} as autorole")
    
    @autorole.command(name="remove", description="remove a role from autorole", usage="[role]", brief="manage_guild", help="config")
    @commands.has_permissions("manage_guild")
    async def autorole_remove(self, ctx: commands.Context, *, role: Union[discord.Role, str]=None): 
      if isinstance(role, str): 
        role = ctx.find_role( role)
        if not role: return await ctx.error(f"No role named **{ctx.message.clean_content[-len(ctx.clean_prefix)+18:]}** found")
      if role:
        check = await self.bot.db.fetchrow("SELECT * FROM autorole WHERE guild_id = {} AND role_id = {}".format(ctx.guild.id, role.id))
        if not check: return await ctx.error(f"{role.mention} is not added")
        await self.bot.db.execute("DELETE FROM autorole WHERE guild_id = {} AND role_id = {}".format(ctx.guild.id, role.id))
        return await ctx.approve(f"Removed {role.mention} from autorole")
    
    @commands.group(invoke_without_command=True, aliases=['rr'])
    async def reactionrole(self, ctx): 
     await ctx.create_pages()
  
    @reactionrole.command(name="add", description="add a reactionrole to a message", brief="manage roles", usage="[message id] [channel] [emoji] [role]", help="config")
    @commands.has_permissions("manage_roles")
    async def rr_add(self, ctx: commands.Context, messageid: int, channel: discord.TextChannel, emoji: Union[discord.Emoji, str], *, role: Union[discord.Role, str]): 
     try: message = await channel.fetch_message(messageid)
     except discord.NotFound: return await ctx.warn("Couldn't find that message")
     if isinstance(role, str): 
      role = ctx.find_role(role)
      if role is None: return await ctx.warn("Couldn't find that role")
     check = await self.bot.db.fetchrow("SELECT * FROM reactionrole WHERE guild_id = $1 AND message_id = $2 AND channel_id = $3 AND emoji_id = $4", ctx.guild.id, message.id, channel.id, emoji.id if isinstance(emoji, discord.Emoji) else ord(str(emoji)))
     if check: return await ctx.warn("A reactionrole with the same arguments is already added to this message")
     try: 
      await message.add_reaction(emoji)
      await self.bot.db.execute("INSERT INTO reactionrole VALUES ($1,$2,$3,$4,$5,$6)", ctx.guild.id, message.id, channel.id, role.id, emoji.id if isinstance(emoji, discord.Emoji) else ord(str(emoji)), str(emoji))   
      return await ctx.approve(f"Added reaction role {emoji} for {role.mention}")
     except: return await ctx.error("Unable to add reaction role for this role")

    @reactionrole.command(name="remove", description="remove a reactionrole from a message", brief="manage roles", usage="[message id] [channel] [emoji]", help="config")
    @commands.has_permissions("manage_roles")
    async def rr_remove(self, ctx: commands.Context, messageid: int, channel: discord.TextChannel, emoji: Union[discord.Emoji, str]): 
     check = await self.bot.db.fetchrow("SELECT * FROM reactionrole WHERE guild_id = $1 AND message_id = $2 AND channel_id = $3 AND emoji_id = $4", ctx.guild.id, messageid, channel.id, emoji.id if isinstance(emoji, discord.Emoji) else ord(str(emoji)))
     if not check: return await ctx.warn("No reaction role found with the given arguments")
     await self.bot.db.execute("DELETE FROM reactionrole WHERE guild_id = $1 AND message_id = $2 AND channel_id = $3 AND emoji_id = $4", ctx.guild.id, messageid, channel.id, emoji.id if isinstance(emoji, discord.Emoji) else ord(str(emoji))) 
     await ctx.approve("Reactionrole sucesfully deleted") 

    @reactionrole.command(name="list", description="list all the reaction roles from the server", help="config")
    async def rr_list(self, ctx: commands.Context):
     results = await self.bot.db.fetch("SELECT * FROM reactionrole WHERE guild_id = $1", ctx.guild.id)
     if len(results) == 0: return await ctx.warn("No **reactionroles** found")
     i=0
     k=1
     l=0
     mes = ""
     number = []
     messages = []
     for result in results:
       mes = f"{mes}`{k}` {result['emoji_text']} - {ctx.guild.get_role(int(result['role_id'])).mention if ctx.guild.get_role(int(result['role_id'])) else result['role_id']} [message link]({(await ctx.guild.get_channel(int(result['channel_id'])).fetch_message(int(result['message_id']))).jump_url or 'https://none.none'})\n"
       k+=1
       l+=1
       if l == 10:
         messages.append(mes)
         number.append(discord.Embed(color=self.bot.color, title=f"reaction roles ({len(results)})", description=messages[i]))
         i+=1
         mes = ""
         l=0

     messages.append(mes)          
     number.append(discord.Embed(color=self.bot.color, title=f"reaction roles ({len(results)})", description=messages[i]))
     await ctx.paginate(number)
    
    @commands.command(aliases=["disablecmd"], description="disable a command", help="config", usage="[command name]")  
    @commands.has_permissions("administrator")
    async def disablecommand(self, ctx: commands.Context, *, cmd: str): 
     command = self.bot.get_command(cmd)
     if not command: return await ctx.warn(f"Couldn't find **{cmd}** command")
     if command.name in ["ping", "help", "uptime", "disablecommand", "disablecmd", "enablecommand", "enablecmd"]: return await ctx.warn("This command can't be disabled")
     check = await self.bot.db.fetchrow("SELECT * FROM disablecommand WHERE command = $1 AND guild_id = $2", command.name, ctx.guild.id)
     if check: return await ctx.error("This command is **already** disabled")
     await self.bot.db.execute("INSERT INTO disablecommand VALUES ($1,$2)", ctx.guild.id, command.name)     
     await ctx.approve(f"Disabled command **{command.name}**")

    @commands.command(aliases=["enablecmd"], help="enable a command that was previously disabled in this server", description="config", usage="[command name]")
    @commands.has_permissions("administrator")
    async def enablecommand(self, ctx: commands.Context, *, cmd: str): 
     command = self.bot.get_command(cmd)
     if not command: return await ctx.warn(f"Couldn't find **{cmd}** command")
     check = await self.bot.db.fetchrow("SELECT * FROM disablecommand WHERE command = $1 AND guild_id = $2", command.name, ctx.guild.id)
     if not check: return await ctx.error("This command is **not** disabled")
     await self.bot.db.execute("DELETE FROM disablecommand WHERE guild_id = $1 AND command = $2", ctx.guild.id, command.name)
     await ctx.approve(f"Enabled command **{command.name}**")
    
    @commands.group(invoke_without_command=True, aliases=["poj"])
    async def pingonjoin(self, ctx): 
      await ctx.create_pages()

    @pingonjoin.command(name="add", description="ping new members when they join your server", help="config", usage="[channel]", brief="manage server")
    @commands.has_permissions("manage_guild")
    async def poj_add(self, ctx: commands.Context, *, channel: discord.TextChannel): 
        check = await self.bot.db.fetchrow("SELECT * FROM pingonjoin WHERE guild_id = $1 AND channel_id = $2", ctx.guild.id, channel.id)
        if check: return await ctx.warn(f"{channel.mention} is already added")
        elif not check: await self.bot.db.execute("INSERT INTO pingonjoin VALUES ($1,$2)", channel.id, ctx.guild.id)
        return await ctx.approve(f"I will ping new members in {channel.mention}")  
    
    @pingonjoin.command(name="remove", description="remove a pingonjoin channel", help="config", usage="<channel>", brief="manage server")
    @commands.has_permissions("manage_guild")
    async def poj_remove(self, ctx: commands.Context, *, channel: discord.TextChannel):  
        check = await self.bot.db.fetchrow("SELECT * FROM pingonjoin WHERE guild_id = $1 AND channel_id = $2", ctx.guild.id, channel.id)
        if not check: return await ctx.error(f"{channel.mention} is not added")
        elif check: await self.bot.db.execute("DELETE FROM pingonjoin WHERE guild_id = $1 AND channel_id = $2", ctx.guild.id, channel.id)
        return await ctx.approve(f"I will not ping new members in {channel.mention}")
    
    @pingonjoin.command(name="list", description="get a list of pingonjoin channels", help="config")
    async def poj_list(self, ctx: commands.Context): 
          i=0
          k=1
          l=0
          mes = ""
          number = []
          messages = []
          results = await self.bot.db.fetch("SELECT * FROM pingonjoin WHERE guild_id = {}".format(ctx.guild.id))
          if not results: return await ctx.error("There are no pingonjoin channels")
          for result in results:
              mes = f"{mes}`{k}` {ctx.guild.get_channel(int(result['channel_id'])).mention if ctx.guild.get_channel(result['channel_id']) else result['channel_id']}\n"
              k+=1
              l+=1
              if l == 10:
               messages.append(mes)
               number.append(Embed(color=self.bot.color, title=f"pingonjoin channels ({len(results)})", description=messages[i]))
               i+=1
               mes = ""
               l=0
    
          messages.append(mes)
          number.append(Embed(color=self.bot.color, title=f"pingonjoin channels ({len(results)})", description=messages[i]))
          await ctx.paginate(number)
    
    @commands.command(description="set a server prefix", help="config", usage="[prefix]", brief="manage server")
    @commands.has_permissions("manage_guild")
    async def prefix(self, ctx: commands.Context, *, prefix: str):
        if len(prefix) > 3: return await ctx.error("Uh! The prefix is too long")
        check = await self.bot.db.fetchrow("SELECT * FROM prefixes WHERE guild_id = $1", ctx.guild.id) 
        if check: await self.bot.db.execute("UPDATE prefixes SET prefix = $1 WHERE guild_id = $2", prefix, ctx.guild.id)
        else: await self.bot.db.execute("INSERT INTO prefixes VALUES ($1, $2)", ctx.guild.id, prefix)
        return await ctx.approve(f"Guild prefix set to `{prefix}`")
    
    @commands.group(invoke_without_command=True, aliases=["fakeperms"])
    async def fakepermissions(self, ctx):
      await ctx.create_pages()
    
    @fakepermissions.command(description="edit fake permissions for a role", help="config", usage="[role]", brief="server owner")
    @server_owner()
    async def edit(self, ctx: commands.Context, *, role: Union[discord.Role, str]): 
     if isinstance(role, str): 
        role = ctx.find_role(role)
        if role is None: return await ctx.warn("This is not a role") 
      
     perms = ["administrator", "manage_guild", "manage_roles", "manage_channels", "manage_messages", "manage_nicknames", "manage_emojis", "ban_members", "kick_members", "moderate_members"]
     options = [discord.SelectOption(label=perm.replace("_", " "), value=perm) for perm in perms]
     embed = discord.Embed(color=self.bot.color, description="🔍 Select the perms that should i add to {}".format(role.mention))
     select = discord.ui.Select(placeholder="select permissions", options=options)
     
     async def select_callback(interaction: discord.Interaction):
      if ctx.author != interaction.user: return await interaction.warn("You are not the author of this message")
      data = json.dumps(select.values)
      check = await self.bot.db.fetchrow("SELECT permissions FROM fake_perms WHERE guild_id = $1 AND role_id = $2", interaction.guild.id, role.id)
      if not check: await self.bot.db.execute("INSERT INTO fake_perms VALUES ($1,$2,$3)", interaction.guild.id, role.id, data)
      else: await self.bot.db.execute("UPDATE fake_perms SET permissions = $1 WHERE guild_id = $2 AND role_id = $3", data, interaction.guild.id, role.id)     
      await interaction.response.edit_message(embed=discord.Embed(color=self.bot.color, description=f"{self.bot.yes} {interaction.user.mention}: Added **{len(select.values)}** permission{'s' if len(select.values) > 1 else ''} to {role.mention}"), view=None)

     select.callback = select_callback 
     view = discord.ui.View()
     view.add_item(select)
     await ctx.reply(embed=embed, view=view)
    
    @fakepermissions.command(name="list", description="list the permissions of a specific role", help="config", usage="[role]")
    async def fakeperms_list(self, ctx: commands.Context, *, role: Union[discord.Role, str]): 
     if isinstance(role, str): 
        role = ctx.find_role(role)
        if role is None: return await ctx.warn("This is not a valid role") 
     
     check = await self.bot.db.fetchrow("SELECT permissions FROM fake_perms WHERE guild_id = $1 AND role_id = $2", ctx.guild.id, role.id)
     if check is None: return await ctx.error("This role has no fake permissions")
     permissions = json.loads(check['permissions'])
     embed = discord.Embed(color=self.bot.color, title=f"@{role.name}'s fake permissions", description="\n".join([f"`{permissions.index(perm)+1}` {perm}" for perm in permissions]))
     embed.set_thumbnail(url=role.display_icon)
     return await ctx.reply(embed=embed)
    
    @fakepermissions.command(aliases=["perms"], description="list all the available permissions", help="config")
    async def permissions(self, ctx: commands.Context): 
      perms = ["administrator", "manage_guild", "manage_roles", "manage_channels", "manage_messages", "manage_nicknames", "manage_emojis", "ban_members", "kick_members", "moderate_members"]
      embed = discord.Embed(color=self.bot.color, description="\n".join([f"`{perms.index(perm)+1}` {perm}" for perm in perms])).set_author(icon_url=self.bot.user.display_avatar.url, name="avaible perms for fakepermissions")
      await ctx.reply(embed=embed)
    
    @commands.group(invoke_without_command=True, description="manage custom punishment responses", help="config")
    async def invoke(self, ctx): 
     await ctx.create_pages()
  
    @invoke.command(name="variables", description="see invoke variables", help="config")
    async def invoke_variables(self, ctx: commands.Context): 
     await ctx.invoke(self.bot.get_command('variables'))
    
    @invoke.command(name="unban", help="config", description='add a custom unban message', usage="[message / embed]", brief="manage server")
    @commands.has_permissions("manage_guild")
    async def invoke_unban(self, ctx: commands.Context, *, code: str):
      await Invoke.invoke_cmds(ctx, ctx.guild.me, code)
    
    @invoke.command(name="ban", help="config", description="add a custom ban message", usage="[message / embed]", brief="manage server")
    @commands.has_permissions("manage_guild")
    async def invoke_ban(self, ctx: commands.Context, *, code: str):
      await Invoke.invoke_cmds(ctx, ctx.guild.me, code) 

    @invoke.command(name="kick", help="config", description="add a custom kick message", usage="[message / embed]", brief="manage server")
    @commands.has_permissions("manage_guild")
    async def invoke_kick(self, ctx: commands.Context, *, code: str):
     await Invoke.invoke_cmds(ctx, ctx.guild.me, code)  
    
    @invoke.command(name="mute", help="config", description="add a custom mute command", brief="manage server", usage="[message / embed]")
    @commands.has_permissions("manage_guild")
    async def invoke_mute(self, ctx: commands.Context, *, code: str):
     await Invoke.invoke_cmds(ctx, ctx.guild.me, code)    
  
    @invoke.command(name="unmute", help="config", description="add a custom unmute command", brief="manage server", usage="[message / embed]")
    @commands.has_permissions("manage_guild")
    async def invoke_unmute(self, ctx: commands.Context, *, code: str):
     await Invoke.invoke_cmds(ctx, ctx.guild.me, code)
    
    @invoke.command(name="jail", help="config", description="add a custom jail command", brief="manage server", usage="[message / embed]")
    @commands.has_permissions("manage_guild")
    async def invoke_jail(self, ctx: commands.Context, *, code: str): 
     await Invoke.invoke_cmds(ctx, ctx.guild.me, code) 
    
    @invoke.command(name="unjail", help="config", description="add a custom unjail command", brief="manage server", usage="[message / embed]")
    @commands.has_permissions("manage_guild")
    async def invoke_unjail(self, ctx: commands.Context, *, code: str): 
     await Invoke.invoke_cmds(ctx, ctx.guild.me, code)
    
async def setup(bot):
    await bot.add_cog(config(bot))