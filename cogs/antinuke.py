import discord, datetime 
from discord.ext import commands 
from tools.whitelist import Whitelist
from tools.predicates import is_antinuke, can_manage, check_whitelist

class antinuke(commands.Cog):
   def __init__(self, bot: commands.AutoShardedBot): 
     self.bot = bot
   
   @commands.group(invoke_without_command=True, name="antinuke", description="protect your server against nukes", aliases=["an"])    
   async def antinuke(self, ctx: commands.Context): 
    return await ctx.create_pages()
   
   @antinuke.command(name="logs", description="configure the logs antinuke channel", brief="antinuke admin", usage="[channel]", help="antinuke") 
   @check_whitelist("antinuke")
   @is_antinuke()
   async def antinuke_logs(self, ctx: commands.Context, *, channel: discord.TextChannel=None): 
    if not channel: 
     await self.bot.db.execute("UPDATE antinuke_toggle SET logs = $1 WHERE guild_id = $2", None, ctx.guild.id)
     return await ctx.approve("Antinuke logging channel has been set to server **owner dms**") 
    await self.bot.db.execute("UPDATE antinuke_toggle SET logs = $1 WHERE guild_id = $2", channel.id, ctx.guild.id)
    return await ctx.approve(f"Antinuke logging channel set to {channel.mention}")
   
   @antinuke.command(name="enable", aliases=["e", "on"], description="enable antinuke in your server", brief="server owner", help="antinuke")
   @can_manage()
   async def antinuke_enable(self, ctx: commands.Context): 
    check = await self.bot.db.fetchrow("SELECT * FROM antinuke_toggle WHERE guild_id = $1", ctx.guild.id)
    if check: return await ctx.warn("AntiNuke is **already** enabled")
    await self.bot.db.execute("INSERT INTO antinuke_toggle (guild_id) VALUES ($1)", ctx.guild.id) 
    return await ctx.approve("AntiNuke has been **enabled**")
   
   @antinuke.command(name="disable", aliases=["d", "off"], description="disable antinuke in your server", brief="server owner", help="antinuke")
   @can_manage()
   @is_antinuke()
   async def antinuke_disable(self, ctx: commands.Context):
    await self.bot.db.execute('DELETE FROM antinuke_toggle WHERE guild_id = $1', ctx.guild.id)
    return await ctx.approve("AntiNuke has been **disabled**") 
   
   @antinuke.group(name="admin", invoke_without_command=True, description="manage antinuke admins", help="antinuke")
   async def antinuke_admin(self, ctx): 
    return await ctx.create_pages()
   
   @antinuke_admin.command(name="add", brief="server owner", description="add an antinuke admin", usage="[member]", help="antinuke")
   @can_manage()
   @is_antinuke()
   async def antinuke_admin_add(self, ctx: commands.Context, *, member: discord.Member): 
    return await Whitelist.whitelist_things(ctx, "antinuke", member) 
   
   @antinuke_admin.command(name="remove", brief="server owner", description="remove an antinuke admin", usage="[member]", help="antinuke")
   @can_manage()
   @is_antinuke()
   async def antinuke_admin_remove(self, ctx: commands.Context, *, member: discord.Member): 
    return await Whitelist.unwhitelist_things(ctx, "antinuke", member)    
   
   @antinuke_admin.command(name="list", help="antinuke", description="returns antinuke admins")   
   @is_antinuke()
   async def antinuke_admin_list(self, ctx: commands.Context): 
    return await Whitelist.whitelisted_things(ctx, "antinuke", "user")
   
   @antinuke.command(name="admins", description="returns antinuke admins", help="antinuke")
   @is_antinuke()
   async def antinuke_admins(self, ctx: commands.Context): 
    return await Whitelist.whitelisted_things(ctx, "antinuke", "user")
   
   @antinuke.command(name="settings", aliases=['stats'], description="check antinuke settings", help="antinuke")
   @is_antinuke()
   async def an_settings(self, ctx: commands.Context): 
    settings_enabled = {"antibot": self.bot.no, "ban": self.bot.no, "channeldelete": self.bot.no, "kick": self.bot.no, "channelcreate": self.bot.no, "roledelete": self.bot.no, "rolecreate": self.bot.no, "mass join": self.bot.no, "new accounts": self.bot.no, "alt join": self.bot.no, "default avatar": self.bot.no} 
    results = await self.bot.db.fetch("SELECT * FROM antinuke WHERE guild_id = $1", ctx.guild.id)
    for result in results: 
      if settings_enabled.get(result['module']): settings_enabled[result['module']] = self.bot.yes
    embed = discord.Embed(color=self.bot.color, description='\n'.join([f'**{m}:** {settings_enabled.get(m)}' for m in ['antibot', 'ban', 'channeldelete', 'kick', 'channelcreate', 'roledelete', 'rolecreate', 'mass join', 'new accounts', 'alt join', 'default avatar']]))
    embed.set_author(name=f"antinuke settings for {ctx.guild.name}") 
    embed.set_thumbnail(url=ctx.guild.icon)
    await ctx.reply(embed=embed)   
   
   @antinuke.group(name="channeldelete", invoke_without_command=True, description="prevent members from deleting the server's channels", help="antinuke")
   async def an_channeldelete(self, ctx): 
    return await ctx.create_pages()
   
   @an_channeldelete.command(name="enable", aliases=['e'], description="enable anti channel delete protection", usage="[punishment]", brief="antinuke admin", help="antinuke")
   @check_whitelist("antinuke")
   @is_antinuke()
   async def an_channeldelete_enable(self, ctx: commands.Context, *, punishment: str): 
    if not punishment in ["ban", "kick", "strip"]: return await ctx.warn(f"Punishment should be either **kick**, **ban** or **strip**, not **{punishment}**")
    check = await self.bot.db.fetchrow("SELECT * FROM antinuke WHERE guild_id = $1 AND module = $2", ctx.guild.id, "channeldelete")
    if not check: await self.bot.db.execute("INSERT INTO antinuke VALUES ($1,$2,$3,$4)", ctx.guild.id, "channeldelete", punishment, 0)
    else: await self.bot.db.execute("UPDATE antinuke SET punishment = $1 WHERE guild_id = $2 AND module = $3", punishment, ctx.guild.id, "channeldelete") 
    return await ctx.approve(f"**Anti channel delete** has been enabled\npunishment: {punishment}\nThreshold: 1 channel deletion per 1 minute")
   
   @an_channeldelete.command(name="disable", aliases=['dis'], description='disable anti channel delete protection', brief="antinuke admin", help="antinuke")
   @check_whitelist("antinuke")
   @is_antinuke()
   async def an_channeldelete_disable(self, ctx: commands.Context): 
     check = await self.bot.db.fetchrow("SELECT * FROM antinuke WHERE guild_id = $1 AND module = $2", ctx.guild.id, "channeldelete")
     if not check: return await ctx.warn("Anti channel delete is **not** enabled")
     await self.bot.db.execute("DELETE FROM antinuke WHERE guild_id = $1 AND module = $2", ctx.guild.id, "channeldelete")
     return await ctx.approve("Antinuke channel delete has been disabled")

   @an_channeldelete.command(name="threshold", usage="[number]", aliases=['limit', 'count'], description="change the number of allowed channel deletions per 1 minute", brief="antinuke admin", help="antinuke")
   @check_whitelist("antinuke")
   @is_antinuke()
   async def an_channeldelete_threshold(self, ctx: commands.Context, number: int): 
    if number < 0: return await ctx.warn("The limit can't be lower than 0") 
    check = await self.bot.db.fetchrow("SELECT * FROM antinuke WHERE guild_id = $1 AND module = $2", ctx.guild.id, "channeldelete")
    if not check: return await ctx.warn("Antinuke channel delete **not** enabled")
    await self.bot.db.execute("UPDATE antinuke SET threshold = $1 WHERE guild_id = $2 AND module = $3", number, ctx.guild.id, "channeldelete")
    return await ctx.approve(f"Antinuke channel delete threshold changed to **{number}** channel deletes per **60** seconds")
   
   @antinuke.group(name="channelcreate", invoke_without_command=True, description="prevent members from creating new channels", help="antinuke")
   async def an_channelcreate(self, ctx): 
    return await ctx.create_pages()
   
   @an_channelcreate.command(name="enable", aliases=['e'], description="enable anti channel create protection", usage="[punishment]", brief="antinuke admin", help="antinuke")
   @check_whitelist("antinuke")
   @is_antinuke()
   async def an_channelcreate_enable(self, ctx: commands.Context, *, punishment: str): 
    if not punishment in ["ban", "kick", "strip"]: return await ctx.warn(f"Punishment should be either **kick**, **ban** or **strip**, not **{punishment}**")
    check = await self.bot.db.fetchrow("SELECT * FROM antinuke WHERE guild_id = $1 AND module = $2", ctx.guild.id, "channelcreate")
    if not check: await self.bot.db.execute("INSERT INTO antinuke VALUES ($1,$2,$3,$4)", ctx.guild.id, "channelcreate", punishment, 0)
    else: await self.bot.db.execute("UPDATE antinuke SET punishment = $1 WHERE guild_id = $2 AND module = $3", punishment, ctx.guild.id, "channelcreate") 
    return await ctx.approve(f"**Anti channel create** has been enabled\npunishment: {punishment}\nThreshold: 1 channel creation per 1 minute")
   
   @an_channelcreate.command(name="disable", aliases=['dis'], description='disable anti channel create protection', brief="antinuke admin", help="antinuke")
   @check_whitelist("antinuke")
   @is_antinuke()
   async def an_channelcreate_disable(self, ctx: commands.Context): 
     check = await self.bot.db.fetchrow("SELECT * FROM antinuke WHERE guild_id = $1 AND module = $2", ctx.guild.id, "channelcreate")
     if not check: return await ctx.warn("Anti channel create is **not** enabled")
     await self.bot.db.execute("DELETE FROM antinuke WHERE guild_id = $1 AND module = $2", ctx.guild.id, "channelcreate")
     return await ctx.approve("Antinuke channel create has been disabled")

   @an_channelcreate.command(name="threshold", usage="[number]", aliases=['limit', 'count'], description="change the number of allowed channel creations per 1 minute", brief="antinuke admin", help="antinuke")
   @check_whitelist("antinuke")
   @is_antinuke()
   async def an_channelcreate_threshold(self, ctx: commands.Context, number: int): 
    if number < 0: return await ctx.warn("The limit can't be lower than 0") 
    check = await self.bot.db.fetchrow("SELECT * FROM antinuke WHERE guild_id = $1 AND module = $2", ctx.guild.id, "channelcreate")
    if not check: return await ctx.warn("Antinuke channel create **not** enabled")
    await self.bot.db.execute("UPDATE antinuke SET threshold = $1 WHERE guild_id = $2 AND module = $3", number, ctx.guild.id, "channelcreate")
    return await ctx.approve(f"Antinuke channel create threshold changed to **{number}** channel creates per **60** seconds")
   
   @antinuke.group(name="rolecreate", invoke_without_command=True, description="prevent members from creating new roles", help="antinuke")
   async def an_rolecreate(self, ctx): 
    return await ctx.create_pages()
   
   @an_rolecreate.command(name="enable", aliases=['e'], description="enable anti role create protection", usage="[punishment]", brief="antinuke admin", help="antinuke")
   @check_whitelist("antinuke")
   @is_antinuke()
   async def an_rolecreate_enable(self, ctx: commands.Context, *, punishment: str): 
    if not punishment in ["ban", "kick", "strip"]: return await ctx.warn(f"Punishment should be either **kick**, **ban** or **strip**, not **{punishment}**")
    check = await self.bot.db.fetchrow("SELECT * FROM antinuke WHERE guild_id = $1 AND module = $2", ctx.guild.id, "rolecreate")
    if not check: await self.bot.db.execute("INSERT INTO antinuke VALUES ($1,$2,$3,$4)", ctx.guild.id, "rolecreate", punishment, 0)
    else: await self.bot.db.execute("UPDATE antinuke SET punishment = $1 WHERE guild_id = $2 AND module = $3", punishment, ctx.guild.id, "rolecreate") 
    return await ctx.approve(f"**Anti role create** has been enabled\npunishment: {punishment}\nThreshold: 1 role creation per 1 minute")
   
   @an_rolecreate.command(name="disable", aliases=['dis'], description='disable anti role create protection', brief="antinuke admin", help="antinuke")
   @check_whitelist("antinuke")
   @is_antinuke()
   async def an_rolecreate_disable(self, ctx: commands.Context): 
     check = await self.bot.db.fetchrow("SELECT * FROM antinuke WHERE guild_id = $1 AND module = $2", ctx.guild.id, "rolecreate")
     if not check: return await ctx.warn("Anti role create is **not** enabled")
     await self.bot.db.execute("DELETE FROM antinuke WHERE guild_id = $1 AND module = $2", ctx.guild.id, "rolecreate")
     return await ctx.approve("Antinuke role create has been disabled")

   @an_rolecreate.command(name="threshold", usage="[number]", aliases=['limit', 'count'], description="change the number of allowed role creations per 1 minute", brief="antinuke admin", help="antinuke")
   @check_whitelist("antinuke")
   @is_antinuke()
   async def an_rolecreate_threshold(self, ctx: commands.Context, number: int): 
    if number < 0: return await ctx.warn("The limit can't be lower than 0") 
    check = await self.bot.db.fetchrow("SELECT * FROM antinuke WHERE guild_id = $1 AND module = $2", ctx.guild.id, "rolecreate")
    if not check: return await ctx.warn("Antinuke role create **not** enabled")
    await self.bot.db.execute("UPDATE antinuke SET threshold = $1 WHERE guild_id = $2 AND module = $3", number, ctx.guild.id, "rolecreate")
    return await ctx.approve(f"Antinuke role create threshold changed to **{number}** role creates per **60** seconds")
   
   @antinuke.group(name="roledelete", invoke_without_command=True, description="prevent members from deleting the server's role", help="antinuke")
   async def an_roledelete(self, ctx): 
    return await ctx.create_pages()
   
   @an_roledelete.command(name="enable", aliases=['e'], description="enable anti role delete protection", usage="[punishment]", brief="antinuke admin", help="antinuke")
   @check_whitelist("antinuke")
   @is_antinuke()
   async def an_roledelete_enable(self, ctx: commands.Context, *, punishment: str): 
    if not punishment in ["ban", "kick", "strip"]: return await ctx.warn(f"Punishment should be either **kick**, **ban** or **strip**, not **{punishment}**")
    check = await self.bot.db.fetchrow("SELECT * FROM antinuke WHERE guild_id = $1 AND module = $2", ctx.guild.id, "roledelete")
    if not check: await self.bot.db.execute("INSERT INTO antinuke VALUES ($1,$2,$3,$4)", ctx.guild.id, "roledelete", punishment, 0)
    else: await self.bot.db.execute("UPDATE antinuke SET punishment = $1 WHERE guild_id = $2 AND module = $3", punishment, ctx.guild.id, "roledelete") 
    return await ctx.approve(f"**Anti role delete** has been enabled\npunishment: {punishment}\nThreshold: 1 role deletion per 1 minute")
   
   @an_roledelete.command(name="disable", aliases=['dis'], description='disable anti role delete protection', brief="antinuke admin", help="antinuke")
   @check_whitelist("antinuke")
   @is_antinuke()
   async def an_roledelete_disable(self, ctx: commands.Context): 
     check = await self.bot.db.fetchrow("SELECT * FROM antinuke WHERE guild_id = $1 AND module = $2", ctx.guild.id, "roledelete")
     if not check: return await ctx.warn("Anti role delete is **not** enabled")
     await self.bot.db.execute("DELETE FROM antinuke WHERE guild_id = $1 AND module = $2", ctx.guild.id, "roledelete")
     return await ctx.approve("Antinuke role delete has been disabled")

   @an_roledelete.command(name="threshold", usage="[number]", aliases=['limit', 'count'], description="change the number of allowed role deletions per 1 minute", brief="antinuke admin", help="antinuke")
   @check_whitelist("antinuke")
   @is_antinuke()
   async def an_roledelete_threshold(self, ctx: commands.Context, number: int): 
    if number < 0: return await ctx.warn("The limit can't be lower than 0") 
    check = await self.bot.db.fetchrow("SELECT * FROM antinuke WHERE guild_id = $1 AND module = $2", ctx.guild.id, "roledelete")
    if not check: return await ctx.warn("Antinuke role delete **not** enabled")
    await self.bot.db.execute("UPDATE antinuke SET threshold = $1 WHERE guild_id = $2 AND module = $3", number, ctx.guild.id, "roledelete")
    return await ctx.approve(f"Antinuke role delete threshold changed to **{number}** role deletes per **60** seconds")
   
   @antinuke.group(name="kick", invoke_without_command=True, description="prevent members from mass kicking the server's members", help="antinuke")
   async def an_kick(self, ctx): 
    return await ctx.create_pages()
   
   @an_kick.command(name="enable", aliases=['e'], description="enable kick members protection", usage="[punishment]", brief="antinuke admin", help="antinuke")
   @check_whitelist("antinuke")
   @is_antinuke()
   async def an_kick_enable(self, ctx: commands.Context, *, punishment: str): 
    if not punishment in ["ban", "kick", "strip"]: return await ctx.warn(f"Punishment should be either **kick**, **ban** or **strip**, not **{punishment}**")
    check = await self.bot.db.fetchrow("SELECT * FROM antinuke WHERE guild_id = $1 AND module = $2", ctx.guild.id, "kick")
    if not check: await self.bot.db.execute("INSERT INTO antinuke VALUES ($1,$2,$3,$4)", ctx.guild.id, "kick", punishment, 0)
    else: await self.bot.db.execute("UPDATE antinuke SET punishment = $1 WHERE guild_id = $2 AND module = $3", punishment, ctx.guild.id, "kick") 
    return await ctx.approve(f"**Anti kick**  has been enabled\npunishment: {punishment}\nThreshold: 1 kick per 1 minute")
   
   @an_kick.command(name="disable", aliases=['dis'], description='disable kick protection', brief="antinuke admin", help="antinuke")
   @check_whitelist("antinuke")
   @is_antinuke()
   async def an_kick_disable(self, ctx: commands.Context): 
     check = await self.bot.db.fetchrow("SELECT * FROM antinuke WHERE guild_id = $1 AND module = $2", ctx.guild.id, "kick")
     if not check: return await ctx.warn("Antinuke kick is **not** enabled")
     await self.bot.db.execute("DELETE FROM antinuke WHERE guild_id = $1 AND module = $2", ctx.guild.id, "kick")
     return await ctx.approve("Antinuke kick has been disabled")

   @an_kick.command(name="threshold", usage="[number]", aliases=['limit', 'count'], description="change the number of allowed kicks per 1 minute", brief="antinuke admin", help="antinuke")
   @check_whitelist("antinuke")
   @is_antinuke()
   async def an_kick_threshold(self, ctx: commands.Context, number: int): 
    if number < 0: return await ctx.warn("The limit can't be lower than 0") 
    check = await self.bot.db.fetchrow("SELECT * FROM antinuke WHERE guild_id = $1 AND module = $2", ctx.guild.id, "kick")
    if not check: return await ctx.warn("Antinuke kick **not** enabled")
    await self.bot.db.execute("UPDATE antinuke SET threshold = $1 WHERE guild_id = $2 AND module = $3", number, ctx.guild.id, "kick")
    return await ctx.approve(f"Antinuke kick threshold changed to **{number}** kicks per **60** seconds")
   
   @antinuke.group(name="ban", invoke_without_command=True, description="prevent members from mass banning the server's members", help="antinuke")
   async def an_ban(self, ctx): 
    return await ctx.create_pages()
   
   @an_ban.command(name="enable", aliases=['e'], description="enable ban members protection", usage="[punishment]", brief="antinuke admin", help="antinuke")
   @check_whitelist("antinuke")
   @is_antinuke()
   async def an_ban_enable(self, ctx: commands.Context, *, punishment: str): 
    if not punishment in ["ban", "kick", "strip"]: return await ctx.warn(f"Punishment should be either **kick**, **ban** or **strip**, not **{punishment}**")
    check = await self.bot.db.fetchrow("SELECT * FROM antinuke WHERE guild_id = $1 AND module = $2", ctx.guild.id, "ban")
    if not check: await self.bot.db.execute("INSERT INTO antinuke VALUES ($1,$2,$3,$4)", ctx.guild.id, "ban", punishment, 0)
    else: await self.bot.db.execute("UPDATE antinuke SET punishment = $1 WHERE guild_id = $2 AND module = $3", punishment, ctx.guild.id, "ban") 
    return await ctx.approve(f"**Antinuke Ban** has been enabled\npunishment: {punishment}\nThreshold: 1 ban per 1 minute")
   
   @an_ban.command(name="disable", aliases=['dis'], description='disable ban protection', brief="antinuke admin", help="antinuke")
   @check_whitelist("antinuke")
   @is_antinuke()
   async def an_ban_disable(self, ctx: commands.Context): 
     check = await self.bot.db.fetchrow("SELECT * FROM antinuke WHERE guild_id = $1 AND module = $2", ctx.guild.id, "ban")
     if not check: return await ctx.warn("Antinuke ban is **not** enabled")
     await self.bot.db.execute("DELETE FROM antinuke WHERE guild_id = $1 AND module = $2", ctx.guild.id, "ban")
     return await ctx.approve("Antinuke ban has been disabled")

   @an_ban.command(name="threshold", usage="[number]", aliases=['limit', 'count'], description="change the number of allowed bans per one minute", brief="antinuke admin", help="antinuke")
   @check_whitelist("antinuke")
   @is_antinuke()
   async def an_ban_threshold(self, ctx: commands.Context, number: int): 
    if number < 0: return await ctx.warn("The limit can't be lower than 0") 
    check = await self.bot.db.fetchrow("SELECT * FROM antinuke WHERE guild_id = $1 AND module = $2", ctx.guild.id, "ban")
    if not check: return await ctx.warn("Antinuke ban **not** enabled")
    await self.bot.db.execute("UPDATE antinuke SET threshold = $1 WHERE guild_id = $2 AND module = $3", number, ctx.guild.id, "ban")
    return await ctx.approve(f"Antinuke ban threshold changed to **{number}** bans per **60** seconds")

   @antinuke.group(name="botadd", aliases=['antibot'], invoke_without_command=True, description="prevent unauthorized bots from joining your server", help="antinuke")
   async def botadd(self, ctx): 
    return await ctx.create_pages()
   
   @botadd.command(name="whitelist", aliases=['wl'], brief="antinuke admin", description="whitelist a bot so it can join the server ", usage="[member]", help="antinuke")
   @check_whitelist("antinuke")
   @is_antinuke()
   async def botadd_whitelist(self, ctx: commands.Context, *, member: discord.User): 
    return await Whitelist.whitelist_things(ctx, "antibot", member) 
   
   @botadd.command(name="unwhitelist", brief="antinuke admin", aliases=['uwl'], description="remove an antibot whitelisted member", usage="[member]", help="antinuke")
   @check_whitelist("antinuke")
   @is_antinuke()
   async def botadd_unwhitelist(self, ctx: commands.Context, *, member: discord.User): 
    return await Whitelist.unwhitelist_things(ctx, "antibot", member)    
   
   @botadd.command(name="whitelisted", description="returns antinuke admins", help="antinuke")   
   @is_antinuke()
   async def botadd_whitelisted(self, ctx: commands.Context): 
    return await Whitelist.whitelisted_things(ctx, "antibot", "user")

   @botadd.command(name="enable", aliases=['e'], description="enable bot adding protection", usage="[punishment]", brief="antinuke admin", help="antinuke")
   @check_whitelist("antinuke")
   @is_antinuke()
   async def botadd_enable(self, ctx: commands.Context, punishment: str): 
    if not punishment in ["ban", "kick", "strip"]: return await ctx.warn(f"Punishment should be either **kick**, **ban** or **strip**, not **{punishment}**")
    check = await self.bot.db.fetchrow("SELECT * FROM antinuke WHERE guild_id = $1 AND module = $2", ctx.guild.id, "antibot")
    if not check: await self.bot.db.execute("INSERT INTO antinuke VALUES ($1,$2,$3,$4)", ctx.guild.id, "antibot", punishment, 0)
    else: await self.bot.db.execute("UPDATE antinuke SET punishment = $1 WHERE guild_id = $2 AND module = $3", punishment, ctx.guild.id, "antibot") 
    return await ctx.approve(f"**Botadd** has been enabled\npunishment: {punishment}")

   @botadd.command(name="disable", aliases=['dis'], description='disable antibot', brief="antinuke admin", help="antinuke")
   @check_whitelist("antinuke")
   @is_antinuke()
   async def botadd_disable(self, ctx: commands.Context): 
     check = await self.bot.db.fetchrow("SELECT * FROM antinuke WHERE guild_id = $1 AND module = $2", ctx.guild.id, "antibot")
     if not check: return await ctx.warn("Antinuke botadd **not** enabled")
     await self.bot.db.execute("DELETE FROM antinuke WHERE guild_id = $1 AND module = $2", ctx.guild.id, "antibot")
     return await ctx.approve("Antinuke botadd has been disabled")
   
   @antinuke.group(invoke_without_command=True, description="prevend join raids", help="antinuke", usage="[enable/disable] [punishment] [joins per 10 seconds]\nexample: antinuke massjoin enable 10")
   async def massjoin(self, ctx: commands.Context): 
      return await ctx.create_pages() 
    
   @massjoin.command(brief="antinuke admin", name="enable", description="prevent join raids", help="antinuke", usage="[punishment] [joins per 10 seconds]\nexample: antinuke massjoin enable ban 10")
   @check_whitelist("antinuke")
   @is_antinuke()
   async def massjoin_enable(self, ctx: commands.Context, punishment: str, joins: int):
     check = await self.bot.db.fetchrow("SELECT * FROM antiraid WHERE guild_id = $1 AND command = $2", ctx.guild.id, "massjoin")         
     if check: return await ctx.warn("Massjoin is **already** enabled")
     await self.bot.db.execute("INSERT INTO antiraid VALUES ($1,$2,$3,$4)", ctx.guild.id, "massjoin", punishment, joins)         
     return await ctx.approve(f"Massjoin is now enabled. This will be triggered only if there are more than **{joins}** joins under **10 seconds**\npunishment: **{punishment}**")
    
   @massjoin.command(brief="antinuke admin", name="disable", description="disable massjoin protection", help="antinuke")
   @check_whitelist("antinuke")
   @is_antinuke()
   async def massjoin_disable(self, ctx: commands.Context):
     check = await self.bot.db.fetchrow("SELECT * FROM antiraid WHERE guild_id = $1 AND command = $2", ctx.guild.id, "massjoin")         
     if not check: return await ctx.warn("Massjoin is **not** enabled")
     await self.bot.db.execute("DELETE FROM antiraid WHERE command = $1 AND guild_id = $2", "massjoin", ctx.guild.id)     
     return await ctx.approve(f"Massjoin been disabled")      
    
   @antinuke.group(invoke_without_command=True, description="prevent alt accounts from joining your server", help="antinuke", usage="[subcommand] [time] [punishment]\nexample: antinuke newaccounts on 2d ban")
   async def newaccounts(self, ctx: commands.Context):
       return await ctx.create_pages()
    
   @newaccounts.command(brief="antinuke admin", name="whitelist", description="let a young account join", help="antinuke", usage="[user]", aliases=['wl'])
   @check_whitelist("antinuke")
   @is_antinuke()
   async def newaccounts_whitelist(self, ctx: commands.Context, *, member: discord.User): 
     check = await ctx.bot.db.fetchrow("SELECT * FROM whitelist WHERE guild_id = $1 AND module = $2 AND object_id = $3 AND mode = $4", ctx.guild.id, "newaccounts", member.id, "user")
     if check: return await ctx.warn(f"**{member}** is **already** whitelisted for **antiraid newaccounts**")
     await ctx.bot.db.execute("INSERT INTO whitelist VALUES ($1,$2,$3,$4)", ctx.guild.id, "newaccounts", member.id, "user")
     return await ctx.approve(f"**{member}** is now whitelisted for **antiraid newaccounts** and can join") 
    
   @newaccounts.command(brief="acomnuke admin", name="unwhitelist", description="remove the whitelist of a new account", help="antinuke", usage="[member]", aliases=['uwl'])
   @check_whitelist("antinuke")
   @is_antinuke()
   async def newaccounts_unwhitelist(self, ctx: commands.Context, *, member: discord.User): 
     check = await ctx.bot.db.fetchrow("SELECT * FROM whitelist WHERE guild_id = $1 AND module = $2 AND object_id = $3 AND mode = $4", ctx.guild.id, "newaccounts", member.id, "user")
     if not check: return await ctx.warn(f"**{member}** is **not** whitelisted for **antiraid newaccounts**")
     await ctx.bot.db.execute("DELETE FROM whitelist WHERE guild_id = $1 AND module = $2 AND object_id = $3 AND mode = $4", ctx.guild.id, "newaccounts", member.id, "user")
     return await ctx.approve(f"**{member}** is no longer whitelisted for **antiraid newaccounts**")   
    
   @newaccounts.command(name="whitelisted", aliases=['list'], description="returns the whitelisted members from the newaccounts antiraid system")
   async def newaccounts_whitelisted(self, ctx: commands.Context): 
     return await Whitelist.whitelisted_things(ctx, "newaccounts", "user") 

   @newaccounts.command(brief="antinuke admin", name="on", description="turn on newaccounts", help="antinuke", usage="[time] [punishment]\nexample: antinuke newaccounts on 2d ban")
   @check_whitelist("antinuke")
   @is_antinuke()
   async def newaccounts_on(self, ctx: commands.Context, time: str, punishment: str):
        try:
         if not punishment in ["kick", "ban"]: return await ctx.error(f"Punishment should be either **kick** or **ban**, not **{punishment}**")
         time = humanfriendly.parse_timespan(time)
         check = await self.bot.db.fetchrow("SELECT * FROM antiraid WHERE guild_id = $1 AND command = $2", ctx.guild.id, "newaccounts")     
         if check: return await ctx.warn("Newaccounts is **already** enabled")
         await self.bot.db.execute("INSERT INTO antiraid VALUES ($1,$2,$3,$4)", ctx.guild.id, "newaccounts", punishment, int(time))         
         return await ctx.approve(f"Newaccounts antiraid enabled ({humanfriendly.format_timespan(time)}) | punishment: {punishment}")
        except humanfriendly.InvalidTimespan: return await ctx.warn(f"**{time}** couldn't be converted in **seconds**")  
    
   @newaccounts.command(brief="antinuke admin", name="off", description="turn off newaccounts", help="antinuke")
   @check_whitelist("antinuke")
   @is_antinuke()
   async def newaccounts_off(self, ctx: commands.Context):
          check = await self.bot.db.fetchrow("SELECT * FROM antiraid WHERE guild_id = $1 AND command = $2", ctx.guild.id, "newaccounts")     
          if check is None: return await ctx.warn("Newaccounts is **not** enabled")
          await self.bot.db.execute('DELETE FROM antiraid WHERE command = $1 AND guild_id = $2', "newaccounts", ctx.guild.id)
          return await ctx.approve("Newaccounts has been disabled")
    
   @antinuke.group(invoke_without_command=True, description="prevent members with no avatar from joining your server", help="antinuke", aliases=["noavatar", "defaultpfp"])
   async def defaultavatar(self, ctx: commands.Context): 
      return await ctx.create_pages()
    
   @defaultavatar.command(brief="antinuke admin", help="antinuke", name="on", description="turn on defaultavatar")
   @check_whitelist("antinuke")
   @is_antinuke()
   async def defaultpfp_on(self, ctx: commands.Context, punishment: str): 
     if not punishment in ["kick", "ban"]: return await ctx.warn("Punishment can be either **ban** or **kick**")
     check = await self.bot.db.fetchrow("SELECT * FROM antiraid WHERE guild_id = $1 AND command = $2", ctx.guild.id, "defaultavatar")   
     if check: return await ctx.warn("Defaultavatar is **already** enabled")
     await self.bot.db.execute("INSERT INTO antiraid VALUES ($1,$2,$3,$4)", ctx.guild.id, "defaultavatar", punishment, None)         
     return await ctx.approve(f"Enabled defaultavatar")   
    
   @defaultavatar.command(brief="antinuke admin", help="antinuke", name="off", description="turn off defaultavatar")
   @check_whitelist("antinuke")
   @is_antinuke()
   async def defaultpfp_off(self, ctx: commands.Context): 
     check = await self.bot.db.fetchrow("SELECT * FROM antiraid WHERE guild_id = $1 AND command = $2", ctx.guild.id, "defaultavatar")   
     if not check: return await ctx.warn("Defaultavatar is **not** enabled")  
     await self.bot.db.execute("DELETE FROM antiraid WHERE guild_id = $1 AND command = $2", ctx.guild.id, "defaultavatar")
     return await ctx.approve("Defaultavatar has been disabled")
    
   @defaultavatar.command(brief="antinuke admin", name="whitelist", description="let a person with no avatar", help="antinuke", usage="[user]", aliases=['wl'])
   @check_whitelist("antinuke")
   @is_antinuke()
   async def defaultavatar_whitelist(self, ctx: commands.Context, *, member: discord.User): 
     check = await ctx.bot.db.fetchrow("SELECT * FROM whitelist WHERE guild_id = $1 AND module = $2 AND object_id = $3 AND mode = $4", ctx.guild.id, "defaultavatar", member.id, "user")
     if check: return await ctx.warn(f"**{member}** is **already** whitelisted for **antiraid defaultavatar**")
     await ctx.bot.db.execute("INSERT INTO whitelist VALUES ($1,$2,$3,$4)", ctx.guild.id, "defaultavatar", member.id, "user")
     return await ctx.approve(f"**{member}** is now whitelisted for **antinuke defaultavatar** and can join")  
    
   @defaultavatar.command(brief="antinuke admin", name="unwhitelist", description="remove the whitelist of a no avatar member", help="antinuke", usage="[member]", aliases=['uwl'])
   @check_whitelist("antinuke")
   @is_antinuke()
   async def defaultavatar_unwhitelist(self, ctx: commands.Context, *, member: discord.User): 
     check = await ctx.bot.db.fetchrow("SELECT * FROM whitelist WHERE guild_id = $1 AND module = $2 AND object_id = $3 AND mode = $4", ctx.guild.id, "defaultavatar", member.id, "user")
     if not check: return await ctx.warn(f"**{member}** is **not** whitelisted for **antiraid defaultavatar**")
     await ctx.bot.db.execute("DELETE FROM whitelist WHERE guild_id = $1 AND module = $2 AND object_id = $3 AND mode = $4", ctx.guild.id, "defaultavatar", member.id, "user")
     return await ctx.approve(f"**{member}** is no longer whitelisted for **aatinuke defaultavatar**")  
    
   @defaultavatar.command(name="whitelisted", aliases=['list'], description="returns the whitelisted members from the defaultavatar antiraid system", help="antinuke")
   @check_whitelist("antinuke")
   @is_antinuke()
   async def defaultavatar_whitelisted(self, ctx: commands.Context): 
     return await Whitelist.whitelisted_things(ctx, "defaultavatar", "user")
   
async def setup(bot: commands.AutoShardedBot) -> None: 
  return await bot.add_cog(antinuke(bot))