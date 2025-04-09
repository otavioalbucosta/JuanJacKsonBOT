import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import datetime
from typing import List, Dict, Optional, Any
from experience.expSystem import ExpSystem


class ExpCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.exp_system = ExpSystem()
    
    # Define o grupo de comandos para experiência
    exp_group = app_commands.Group(name="exp", description="Comandos para gerenciar experiência de RPG")
    
    @exp_group.command(name="create", description="Inicia uma nova ficha de experiência para a sessão")
    async def create_session(self, interaction: discord.Interaction):
        """Cria uma nova ficha de experiência"""
        guild_id = interaction.guild_id
        
        # Verificar se já existe uma ficha ativa com conteúdo
        active_session = self.exp_system.get_active_session(guild_id)
        if active_session and (active_session.party_entries or active_session.players):
            await interaction.response.send_message(
                "❌ Já existe uma ficha de experiência ativa neste servidor! Finalize a atual antes de criar uma nova.\n"
                "Use `/exp preview` para ver a ficha atual, `/exp finalize [nome]` para finalizá-la ou `/exp clear_session` para apagá-la.",
                ephemeral=True
            )
            return
            
        self.exp_system.create_session(guild_id)
        await interaction.response.send_message("✅ Nova ficha de experiência criada para a sessão atual!")
    
    @exp_group.command(name="add_party", description="Adiciona experiência para todo o grupo")
    @app_commands.describe(
        amount="Quantidade de experiência",
        achievement="Descrição do feito que gerou a experiência"
    )
    async def add_party_exp(self, interaction: discord.Interaction, amount: int, achievement: str):
        """Adiciona experiência para o grupo todo"""
        guild_id = interaction.guild_id
        entry = self.exp_system.add_party_exp(guild_id, amount, achievement)
        
        # Formatar hora para exibição
        timestamp = datetime.datetime.fromisoformat(entry.timestamp).strftime("%H:%M")
        
        await interaction.response.send_message(
            f"✨ **EXP Coletiva Adicionada!**\n"
            f"**Quantidade:** {amount} XP\n"
            f"**Feito:** {achievement}\n"
            f"**Horário:** {timestamp}\n\n"
            f"Esta experiência será compartilhada com todos os jogadores da sessão."
        )
    
    @exp_group.command(name="add_player", description="Adiciona experiência para um jogador específico")
    @app_commands.describe(
        character_name="Nome do personagem",
        amount="Quantidade de experiência",
        achievement="Descrição do feito que gerou a experiência"
    )
    async def add_player_exp(self, interaction: discord.Interaction, character_name: str, amount: int, achievement: str):
        """Adiciona experiência para um jogador específico"""
        guild_id = interaction.guild_id
        entry = self.exp_system.add_player_exp(guild_id, character_name, amount, achievement)
        
        # Formatar hora para exibição
        timestamp = datetime.datetime.fromisoformat(entry.timestamp).strftime("%H:%M")
        
        await interaction.response.send_message(
            f"✨ **EXP Individual Adicionada!**\n"
            f"**Jogador:** {character_name}\n"
            f"**Quantidade:** {amount} XP\n"
            f"**Feito:** {achievement}\n"
            f"**Horário:** {timestamp}"
        )
    
    @exp_group.command(name="remove_party", description="Remove uma entrada de experiência coletiva")
    @app_commands.describe(
        index="Índice da entrada a ser removida (veja em /exp preview)"
    )
    async def remove_party_exp(self, interaction: discord.Interaction, index: int):
        """Remove uma entrada de experiência coletiva"""
        guild_id = interaction.guild_id
        # Índices no Discord começam em 1 para melhor usabilidade
        adjusted_index = index - 1
        
        entry = self.exp_system.remove_party_exp(guild_id, adjusted_index)
        if entry:
            await interaction.response.send_message(
                f"❌ **EXP Coletiva Removida!**\n"
                f"**Quantidade:** {entry.amount} XP\n"
                f"**Feito:** {entry.achievement}"
            )
        else:
            await interaction.response.send_message(
                f"❌ Entrada não encontrada. Use `/exp preview` para ver os índices corretos.",
                ephemeral=True
            )
    
    @exp_group.command(name="remove_player", description="Remove uma entrada de experiência individual")
    @app_commands.describe(
        character_name="Nome do personagem",
        index="Índice da entrada a ser removida (veja em /exp preview)"
    )
    async def remove_player_exp(self, interaction: discord.Interaction, character_name: str, index: int):
        """Remove uma entrada de experiência individual"""
        guild_id = interaction.guild_id
        # Índices no Discord começam em 1 para melhor usabilidade
        adjusted_index = index - 1
        
        entry = self.exp_system.remove_player_exp(guild_id, character_name, adjusted_index)
        if entry:
            await interaction.response.send_message(
                f"❌ **EXP Individual Removida!**\n"
                f"**Jogador:** {character_name}\n"
                f"**Quantidade:** {entry.amount} XP\n"
                f"**Feito:** {entry.achievement}"
            )
        else:
            await interaction.response.send_message(
                f"❌ Entrada não encontrada. Verifique o nome do personagem e o índice.",
                ephemeral=True
            )
    
    @exp_group.command(name="preview", description="Mostra um resumo da ficha de experiência atual")
    async def preview_session(self, interaction: discord.Interaction):
        """Mostra uma prévia da ficha de experiência atual"""
        guild_id = interaction.guild_id
        session = self.exp_system.get_active_session(guild_id)
        
        # Criar embed para mostrar os dados
        embed = discord.Embed(
            title="📝 Prévia da Ficha de Experiência",
            description="Resumo parcial da experiência registrada nesta sessão",
            color=discord.Color.gold()
        )
        
        # Adicionar experiência do grupo
        party_text = ""
        if session.party_entries:
            for i, entry in enumerate(session.party_entries):
                # +1 no índice para ser mais amigável
                party_text += f"{i+1}. **{entry.amount} XP** - {entry.achievement}\n"
            party_total = session.get_party_total()
            party_text += f"\n**Total Coletivo: {party_total} XP**"
        else:
            party_text = "*Nenhuma experiência coletiva registrada*"
        
        embed.add_field(name="📊 Experiência Coletiva", value=party_text, inline=False)
        
        # Adicionar experiência individual por jogador
        if session.players:
            for name, player in session.players.items():
                player_text = ""
                for i, entry in enumerate(player.entries):
                    # +1 no índice para ser mais amigável
                    player_text += f"{i+1}. **{entry.amount} XP** - {entry.achievement}\n"
                player_total = player.get_total()
                player_text += f"\n**Total Individual: {player_total} XP**"
                embed.add_field(name=f"👤 {name}", value=player_text, inline=False)
        else:
            embed.add_field(name="👤 Experiência Individual", value="*Nenhuma experiência individual registrada*", inline=False)
        
        # Adicionar totais gerais
        grand_totals = session.get_grand_totals()
        if grand_totals:
            totals_text = "\n".join([f"**{name}:** {total} XP" for name, total in grand_totals.items()])
            embed.add_field(name="🏆 Totais Gerais (Coletivo + Individual)", value=totals_text, inline=False)
        
        # Adicionar rodapé com instruções
        embed.set_footer(text="Use /exp finalize [nome_da_sessão] para finalizar e salvar esta ficha")
        
        await interaction.response.send_message(embed=embed)
    
    @exp_group.command(name="finalize", description="Finaliza e salva a ficha de experiência da sessão")
    @app_commands.describe(
        session_name="Nome/título da sessão para identificar a ficha"
    )
    async def finalize_session(self, interaction: discord.Interaction, session_name: str):
        """Finaliza a sessão atual e salva no histórico"""
        guild_id = interaction.guild_id
        # Verificar se a sessão tem algum conteúdo
        session = self.exp_system.get_active_session(guild_id)
        if not session.party_entries and not session.players:
            await interaction.response.send_message(
                "❌ A ficha de experiência está vazia! Adicione alguma experiência antes de finalizar.",
                ephemeral=True
            )
            return
        
        # Verificar se o nome já existe
        server_history = self.exp_system.get_history(guild_id)
        if session_name in server_history:
            await interaction.response.send_message(
                f"❌ Já existe uma sessão com o nome '{session_name}'. Escolha outro nome.",
                ephemeral=True
            )
            return
        
        success = self.exp_system.finalize_session(guild_id, session_name)
        if not success:
            await interaction.response.send_message(
                "❌ Ocorreu um erro ao finalizar a sessão. Verifique o nome e tente novamente.",
                ephemeral=True
            )
            return
        
        # Criar embed com o resumo final
        embed = discord.Embed(
            title=f"🧾 Nota Fiscal de Experiência: {session_name}",
            description=f"Resumo final de experiência da sessão",
            color=discord.Color.green()
        )
        
        # Adicionar experiência do grupo
        party_text = ""
        if session.party_entries:
            for entry in session.party_entries:
                party_text += f"**{entry.amount} XP** - {entry.achievement}\n"
            party_total = session.get_party_total()
            party_text += f"\n**Total Coletivo: {party_total} XP**"
        else:
            party_text = "*Nenhuma experiência coletiva registrada*"
        
        embed.add_field(name="📊 Experiência Coletiva", value=party_text, inline=False)
        
        # Adicionar experiência individual por jogador
        if session.players:
            for name, player in session.players.items():
                player_text = ""
                for entry in player.entries:
                    player_text += f"**{entry.amount} XP** - {entry.achievement}\n"
                player_total = player.get_total()
                player_text += f"\n**Total Individual: {player_total} XP**"
                embed.add_field(name=f"👤 {name}", value=player_text, inline=False)
        
        # Adicionar totais gerais
        grand_totals = session.get_grand_totals()
        if grand_totals:
            totals_text = "\n".join([f"**{name}:** {total} XP" for name, total in grand_totals.items()])
            embed.add_field(name="🏆 Totais Gerais (Coletivo + Individual)", value=totals_text, inline=False)
        
        # Adicionar data da sessão no rodapé
        created_date = datetime.datetime.fromisoformat(session.creation_date).strftime("%d/%m/%Y")
        embed.set_footer(text=f"Sessão realizada em {created_date}")
        
        await interaction.response.send_message(
            content="✅ **Nota fiscal de experiência finalizada e salva com sucesso!**",
            embed=embed
        )
    
    @exp_group.command(name="clear_session", description="Apaga a ficha de experiência ativa")
    async def clear_session(self, interaction: discord.Interaction):
        """Apaga a ficha de experiência ativa"""
        guild_id = interaction.guild_id
        
        # Verificar se existe uma ficha ativa com conteúdo
        active_session = self.exp_system.get_active_session(guild_id)
        if not active_session or (not active_session.party_entries and not active_session.players):
            await interaction.response.send_message(
                "❌ Não existe uma ficha de experiência ativa com conteúdo para ser apagada.",
                ephemeral=True
            )
            return
            
        # Pedir confirmação antes de apagar
        confirm_view = discord.ui.View()
        confirm_button = discord.ui.Button(label="Confirmar", style=discord.ButtonStyle.danger)
        cancel_button = discord.ui.Button(label="Cancelar", style=discord.ButtonStyle.secondary)
        
        async def confirm_callback(interaction: discord.Interaction):
            self.exp_system.create_session(guild_id)  # Isso substitui a sessão atual por uma nova vazia
            await interaction.response.send_message("🗑️ Ficha de experiência ativa apagada com sucesso!")
            confirm_view.stop()
            
        async def cancel_callback(interaction: discord.Interaction):
            await interaction.response.send_message("❌ Operação cancelada.", ephemeral=True)
            confirm_view.stop()
            
        confirm_button.callback = confirm_callback
        cancel_button.callback = cancel_callback
        confirm_view.add_item(confirm_button)
        confirm_view.add_item(cancel_button)
        
        await interaction.response.send_message(
            "⚠️ **ATENÇÃO**: Você está prestes a apagar a ficha de experiência ativa. Esta ação não pode ser desfeita.\n"
            "Deseja continuar?",
            view=confirm_view,
            ephemeral=True
        )
    
    @exp_group.command(name="history", description="Mostra o histórico de fichas de experiência")
    @app_commands.describe(
        session_name="Nome da sessão específica (opcional)"
    )
    async def show_history(self, interaction: discord.Interaction, session_name: Optional[str] = None):
        """Mostra o histórico de experiência"""
        guild_id = interaction.guild_id
        server_history = self.exp_system.get_history(guild_id)
        
        if not server_history:
            await interaction.response.send_message(
                "📚 Não há histórico de sessões salvas ainda neste servidor.",
                ephemeral=True
            )
            return
        
        # Se um nome específico foi fornecido
        if session_name:
            session = self.exp_system.get_session_by_name(guild_id, session_name)
            if not session:
                await interaction.response.send_message(
                    f"❌ Sessão '{session_name}' não encontrada no histórico deste servidor.",
                    ephemeral=True
                )
                return
            
            # Criar embed com o resumo da sessão específica
            embed = discord.Embed(
                title=f"🧾 Nota Fiscal de Experiência: {session_name}",
                description=f"Resumo de experiência da sessão salva",
                color=discord.Color.blue()
            )
            
            # Adicionar experiência do grupo
            party_text = ""
            if session.party_entries:
                for entry in session.party_entries:
                    party_text += f"**{entry.amount} XP** - {entry.achievement}\n"
                party_total = session.get_party_total()
                party_text += f"\n**Total Coletivo: {party_total} XP**"
            else:
                party_text = "*Nenhuma experiência coletiva registrada*"
            
            embed.add_field(name="📊 Experiência Coletiva", value=party_text, inline=False)
            
            # Adicionar experiência individual por jogador
            if session.players:
                for name, player in session.players.items():
                    player_text = ""
                    for entry in player.entries:
                        player_text += f"**{entry.amount} XP** - {entry.achievement}\n"
                    player_total = player.get_total()
                    player_text += f"\n**Total Individual: {player_total} XP**"
                    embed.add_field(name=f"👤 {name}", value=player_text, inline=False)
            
            # Adicionar totais gerais
            grand_totals = session.get_grand_totals()
            if grand_totals:
                totals_text = "\n".join([f"**{name}:** {total} XP" for name, total in grand_totals.items()])
                embed.add_field(name="🏆 Totais Gerais (Coletivo + Individual)", value=totals_text, inline=False)
            
            # Adicionar data da sessão no rodapé
            created_date = datetime.datetime.fromisoformat(session.creation_date).strftime("%d/%m/%Y")
            embed.set_footer(text=f"Sessão realizada em {created_date}")
            
            await interaction.response.send_message(embed=embed)
        else:
            # Listar todas as sessões do histórico
            sessions = self.exp_system.get_all_session_names(guild_id)
            
            embed = discord.Embed(
                title="📚 Histórico de Sessões",
                description="Lista de todas as sessões salvas neste servidor",
                color=discord.Color.blue()
            )
            
            sessions_text = "\n".join([f"• **{name}**" for name in sessions])
            embed.add_field(name="Sessões Disponíveis", value=sessions_text)
            embed.set_footer(text="Use /exp history [nome_da_sessão] para ver os detalhes de uma sessão específica")
            
            await interaction.response.send_message(embed=embed)