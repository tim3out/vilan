import discord, emoji, re
from discord.ext import commands

class br:
   class Name(discord.ui.Modal, title="change your booster role name"):
      name = discord.ui.TextInput(
        label="role name",
        placeholder="type your new role name here",
        style=discord.TextStyle.short,
        required=True
     )
      
      async def on_submit(self, interaction: discord.Interaction):
         check = await interaction.client.db.fetchrow("SELECT * FROM booster_roles WHERE guild_id = $1 AND user_id = $2", interaction.guild.id, interaction.user.id)
         if not check: return await interaction.warn("You do not have a **booster role** created. Use `boosterrole create` to create one")
         role = interaction.guild.get_role(check["role_id"])
         await role.edit(name=self.name.value)
         return await interaction.approve("Changed your **booster role** name to **{}**".format(self.name.value))
    
   class Icon(discord.ui.Modal, title="change the booster role icon"):
      name = discord.ui.TextInput(
        label='role icon',
        placeholder='this should be an emoji',
        style=discord.TextStyle.short,
        required=True
    )

      async def on_submit(self, interaction: discord.Interaction):
       try: 
         check = await interaction.client.db.fetchrow("SELECT * FROM booster_roles WHERE guild_id = {} AND user_id = {}".format(interaction.guild.id, interaction.user.id))         
         if not check: return await interaction.warn("You don't have a booster role. Use `boosterrole create` to create one")
         role = interaction.guild.get_role(check['role_id'])
         icon = ""
         if emoji.is_emoji(self.name.value): icon = self.name.value 
         else:
          emojis = re.findall(r'<(?P<animated>a?):(?P<name>[a-zA-Z0-9_]{2,32}):(?P<id>[0-9]{18,22})>', self.name.value)
          emoj = emojis[0]
          format = ".gif" if emoj[0] == "a" else ".png"
          url = "https://cdn.discordapp.com/emojis/{}{}".format(emoj[2], format)
          icon = await interaction.client.session.read(url)
         await role.edit(display_icon=icon) 
         return await interaction.approve("Changed your **booster role** icon")  
       except: return await interaction.error("Unable to change the role icon")
   
   class Color(discord.ui.Modal, title="change the booster role color"):
      name = discord.ui.TextInput(
        label='role color',
        placeholder='this should be a hex code',
        style=discord.TextStyle.short,
        required=True
    )

      async def on_submit(self, interaction: discord.Interaction):
       try: 
         check = await interaction.client.db.fetchrow("SELECT * FROM booster_roles WHERE guild_id = {} AND user_id = {}".format(interaction.guild.id, interaction.user.id))         
         if not check: return await interaction.warn("You don't have a booster role. Use `boosterrole create` to create one")
         role = interaction.guild.get_role(check['role_id'])
         color = self.name.value.replace("#", "")
         color = int(color, 16)
         await role.edit(color=color)
         return await interaction.approve("Changed your **booster role** color")
       except: return await interaction.error("Unable to change the role color")
   
   class Position(discord.ui.Modal, title="change your booster role position"):
      name = discord.ui.TextInput(
        label="role position",
        placeholder="you new role position here",
        style=discord.TextStyle.short,
        required=True
     )
      
      async def on_submit(self, interaction: discord.Interaction):
         check = await interaction.client.db.fetchrow("SELECT * FROM booster_roles WHERE guild_id = $1 AND user_id = $2", interaction.guild.id, interaction.user.id)
         if not check: return await interaction.warn("You do not have a **booster role** created. Use `boosterrole create` to create one")
         role = interaction.guild.get_role(check["role_id"])
         if role.position >= interaction.guild.get_member(interaction.client.user.id).top_role.position: return await interaction.warn("I cannot managed this role")
         if int(self.name.value) == 0: return await interaction.warn("Position cannot be lower than 1")
         await role.edit(position=int(self.name.value))
         return await interaction.approve("Changed your **booster role** position to **{}**".format(int(self.name.value)))