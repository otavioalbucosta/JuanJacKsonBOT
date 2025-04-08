# Correção do código principal para usar slash commands
import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv

from initiativeCommands import InitiativeCommands

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Define intents para o bot
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True  # Importante para detectar reações!

# Classe do bot corrigida
class RPGBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='$', intents=intents)
    
    async def setup_hook(self):
        # Registrar os cogs
        await self.add_cog(InitiativeCommands(self))
        
        # Sincronizar comandos com o Discord - esta linha é crucial!
        print("Sincronizando comandos com o Discord...")
        
        # Sincronize para cada guild específica em vez de globalmente
        # Isso faz com que os comandos apareçam mais rapidamente (quase instantaneamente)
        for guild in self.guilds:
            await self.tree.sync(guild=discord.Object(id=guild.id))
            print(f"Comandos sincronizados para: {guild.name}")
        
        # Opcionalmente, sincronize globalmente também
        await self.tree.sync()
        print("Comandos sincronizados globalmente!")
    
    async def on_ready(self):
        print(f'Bot conectado como {self.user}')
        print(f'ID do bot: {self.user.id}')
        print('Servidores conectados:')
        for guild in self.guilds:
            print(f'- {guild.name} (ID: {guild.id})')
        print('-------------------')

    async def sync_commands_with_guild(self, guild_id=None):
        """Sincroniza comandos com uma guild específica ou globalmente"""
        if guild_id:
            self.tree.clear_commands(guild=discord.Object(id=guild_id))
            await self.tree.sync(guild=discord.Object(id=guild_id))
            print(f"Comandos limpos e sincronizados para guild ID: {guild_id}")
        else:
            self.tree.clear_commands()
            await self.tree.sync()
            print("Comandos limpos e sincronizados globalmente")

    # Use este comando temporário para forçar sincronização


# Inicializa o bot
bot = RPGBot()

# Executa o bot
token = os.getenv("DISCORD_TOKEN")
if not token:
    raise ValueError("Token do Discord não encontrado. Verifique seu arquivo .env")

bot.run(token)