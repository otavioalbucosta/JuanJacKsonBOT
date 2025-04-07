# Modificação do código principal
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from initiativeCommands import InitiativeCommands

from keep_alive import keep_alive

# Define intents para o bot
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True  # Importante para detectar reações!

load_dotenv()
keep_alive()

# Prefixo do bot para comandos
bot = commands.Bot(command_prefix='$', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')
    print('-------------------')
    # Carrega o módulo de iniciativa
    await bot.add_cog(InitiativeCommands(bot))

@bot.command(name='msg')
async def mensagem(ctx, *, texto=None):
    """Envia uma mensagem para o canal atual e apaga a mensagem original"""
    # Apaga a mensagem que chamou o comando
    user = ctx.message.author
    await ctx.message.delete()
    if texto:
        await ctx.send(texto)

@bot.command(name='driscol')
async def driscol(ctx):
    await ctx.send(f"DRISCOOOOOOL!")



# Executa o bot com o token
token = os.getenv("DISCORD_TOKEN") 
bot.run(token)