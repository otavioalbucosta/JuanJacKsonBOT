# Modificação do código principal
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from initiativeCommands import InitiativeCommands

# Define intents para o bot
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True  # Importante para detectar reações!

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
bot.run("MTM1ODIwNDk0ODk3Mzc0ODQ4Nw.GSBuq_.NIGAxW36gqLhssAR5XDPFiVUi3CokCwgf03wy0")