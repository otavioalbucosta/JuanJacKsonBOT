import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio
from dotenv import load_dotenv

from Initiative.initiativeCommands import InitiativeCommands
from experience.expCommands import ExpCommands

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Define intents para o bot
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True  # Importante para detectar reações!

# Classe do bot refatorada
class RPGBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='$', intents=intents)
    
    async def setup_hook(self):
        # Registrar os cogs
        await self.add_cog(InitiativeCommands(self))
        await self.add_cog(ExpCommands(self))
        print("Cogs registrados com sucesso.")
        
        # Sincronizar comandos para todos os servidores
        print("Iniciando sincronização de comandos com todos os servidores...")
        await self.sync_all_commands()
    
    async def sync_all_commands(self):
        """Sincroniza comandos em todos os servidores onde o bot está presente"""
        # Primeiro, sincronize para cada guild específica
        sync_tasks = []
        for guild in self.guilds:
            print(f"Sincronizando comandos para: {guild.name} (ID: {guild.id})...")
            task = asyncio.create_task(self.tree.sync(guild=discord.Object(id=guild.id)))
            sync_tasks.append((guild.name, task))
        
        # Aguarde todas as sincronizações terminarem
        for guild_name, task in sync_tasks:
            try:
                await task
                print(f"✓ Comandos sincronizados para: {guild_name}")
            except Exception as e:
                print(f"✗ Erro ao sincronizar comandos para {guild_name}: {str(e)}")
        
        # Sincronize globalmente também para garantir compatibilidade
        try:
            await self.tree.sync()
            print("✓ Comandos sincronizados globalmente com sucesso!")
        except Exception as e:
            print(f"✗ Erro ao sincronizar comandos globalmente: {str(e)}")
    
    async def on_ready(self):
        print(f'Bot conectado como {self.user}')
        print(f'ID do bot: {self.user.id}')
        print('Servidores conectados:')
        for guild in self.guilds:
            print(f'- {guild.name} (ID: {guild.id})')
        print('-------------------')

    async def on_guild_join(self, guild):
        """Sincroniza comandos automaticamente quando o bot entra em um novo servidor"""
        print(f"Bot adicionado ao servidor: {guild.name} (ID: {guild.id})")
        try:
            await self.tree.sync(guild=discord.Object(id=guild.id))
            print(f"✓ Comandos sincronizados automaticamente para o novo servidor: {guild.name}")
        except Exception as e:
            print(f"✗ Erro ao sincronizar comandos para o novo servidor {guild.name}: {str(e)}")

    @commands.command(name='sync')
    @commands.is_owner()
    async def sync_command(self, ctx, option: str = None):
        """Sincroniza manualmente os comandos slash com o Discord.
        
        Opções:
        - guild: sincroniza apenas para o servidor atual
        - global: sincroniza globalmente
        - all: sincroniza para todos os servidores e globalmente (padrão)
        """
        await ctx.send("🔄 Iniciando sincronização de comandos...")
        
        if option == 'guild':
            try:
                await self.tree.sync(guild=ctx.guild)
                await ctx.send(f"✅ Comandos sincronizados localmente para: {ctx.guild.name}")
            except Exception as e:
                await ctx.send(f"❌ Erro ao sincronizar: {str(e)}")
            return
            
        elif option == 'global':
            try:
                await self.tree.sync()
                await ctx.send("✅ Comandos sincronizados globalmente")
            except Exception as e:
                await ctx.send(f"❌ Erro ao sincronizar: {str(e)}")
            return
            
        # Opção padrão: sincronizar todos (all)
        await self.sync_all_commands()
        await ctx.send("✅ Comandos sincronizados para todos os servidores e globalmente!")

# Inicializa e executa o bot
if __name__ == "__main__":
    bot = RPGBot()
    token = os.getenv("DISCORD_TOKEN")
    
    if not token:
        raise ValueError("Token do Discord não encontrado. Verifique seu arquivo .env")
    
    print("Iniciando bot...")
    bot.run(token)