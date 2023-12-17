import discord
from discord.ext import commands

class PgView(discord.ui.View):
    def __init__(self, ctx: commands.Context, embeds: list):
      super().__init__()
      self.embeds = embeds
      self.ctx = ctx
      self.p = 0
    
    async def interaction_check(self, interaction):
      if interaction.user.id != self.ctx.author.id:
        await interaction.warn("You can't interact with this")
        return False
      return True
    
    @discord.ui.button(emoji="<:left:1115966984165797969>", style=discord.ButtonStyle.gray)
    async def left(self, interaction: discord.Interaction, button: discord.ui.Button):
      if self.p == 0:
        await interaction.response.edit_message(embed=self.embeds[-1])
        self.p = len(self.embeds)-1
        return
      self.p = self.p-1
      await interaction.response.edit_message(embed=self.embeds[self.p])
    
    @discord.ui.button(emoji="<:stop2:1115969501138260069>", style=discord.ButtonStyle.gray)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
      return await interaction.message.delete()
    
    @discord.ui.button(emoji="<:right:1115967005481250828>", style=discord.ButtonStyle.gray)
    async def right(self, interaction: discord.Interaction, button: discord.ui.Button):
      if self.p == len(self.embeds)-1:
        await interaction.response.edit_message(embed=self.embeds[0])
        self.p = 0
        return
      self.p = self.p + 1
      await interaction.response.edit_message(embed=self.embeds[self.p])
    
    async def on_timeout(self) -> None: 
        mes = await self.message.channel.fetch_message(self.message.id)
        if not mes: return
        if len(mes.components) == 0: return
        for item in self.children:
            item.disabled = True

        try: await self.message.edit(view=self)   
        except: return