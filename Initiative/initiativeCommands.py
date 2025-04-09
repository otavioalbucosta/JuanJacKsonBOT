import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from typing import Dict
from Initiative.initiativeQueue import InitiativeTracker
from Initiative.character import Character
from Initiative.effects import Effect
import json
import os.path


# Emojis para controle via reações
NEXT_TURN_EMOJI = "⏩"
START_COMBAT_EMOJI = "▶️"
END_COMBAT_EMOJI = "⏹️"
CLEAR_LIST_EMOJI = "🧹"

# Lista de emojis para adicionar às mensagens
CONTROL_EMOJIS = [NEXT_TURN_EMOJI, START_COMBAT_EMOJI, END_COMBAT_EMOJI, CLEAR_LIST_EMOJI]

# Diretório para salvar os dados do tracker
DATA_DIR = "bot_data"
TRACKER_FILE = "initiative_tracker_{}.json"

# Comandos para o bot relacionados à iniciativa
class InitiativeCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.trackers: Dict[int, InitiativeTracker] = {}  # Um tracker por canal
        self.active_messages: Dict[int, int] = {}  # Mapeia mensagens para canais
        
        # Certifica-se de que o diretório de dados existe
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
        
        # Carrega trackers salvos anteriormente
        self.load_all_trackers()
    
    def get_tracker(self, channel_id: int) -> InitiativeTracker:
        """Obtém (ou cria) um tracker para o canal específico"""
        if channel_id not in self.trackers:
            self.trackers[channel_id] = InitiativeTracker()
            # Tenta carregar do arquivo
            self.load_tracker(channel_id)
        return self.trackers[channel_id]
    
    def save_tracker(self, channel_id: int):
        """Salva o estado do tracker para um canal específico em JSON"""
        tracker = self.trackers.get(channel_id)
        if tracker:
            filepath = os.path.join(DATA_DIR, TRACKER_FILE.format(channel_id))
            try:
                # Converter para dicionário e salvar como JSON
                tracker_dict = tracker.to_dict()
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(tracker_dict, f, ensure_ascii=False, indent=2)
                print(f"Tracker para o canal {channel_id} salvo em JSON com sucesso!")
            except Exception as e:
                print(f"Erro ao salvar tracker JSON para o canal {channel_id}: {e}")
    
    def load_tracker(self, channel_id: int) -> bool:
        """Carrega o estado do tracker para um canal específico a partir de JSON"""
        filepath = os.path.join(DATA_DIR, TRACKER_FILE.format(channel_id))
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    tracker_dict = json.load(f)
                
                # Criar tracker a partir do dicionário
                self.trackers[channel_id] = InitiativeTracker.from_dict(tracker_dict)
                print(f"Tracker para o canal {channel_id} carregado do JSON com sucesso!")
                return True
            except Exception as e:
                print(f"Erro ao carregar tracker JSON para o canal {channel_id}: {e}")
        return False
    
    def load_all_trackers(self):
        """Carrega todos os trackers salvos em JSON"""
        if os.path.exists(DATA_DIR):
            for filename in os.listdir(DATA_DIR):
                if filename.startswith("initiative_tracker_") and filename.endswith(".json"):
                    try:
                        channel_id = int(filename.replace("initiative_tracker_", "").replace(".json", ""))
                        self.load_tracker(channel_id)
                    except ValueError:
                        continue
    
    async def delete_previous_message(self, channel, tracker):
        """Deleta a mensagem anterior da fila de iniciativa, se existir"""
        if tracker.last_message_id:
            try:
                # Tenta buscar e deletar a mensagem anterior
                message = await channel.fetch_message(tracker.last_message_id)
                await message.delete()
                
                # Remove o mapeamento desta mensagem
                if message.id in self.active_messages:
                    del self.active_messages[message.id]
                
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                # Ignora erros se a mensagem já não existe ou não pode ser deletada
                pass
            
            # Limpa o ID da última mensagem no tracker
            tracker.last_message_id = None
    
    async def send_initiative_message(self, interaction_or_ctx, tracker):
        """Envia uma nova mensagem de iniciativa com reações após deletar a antiga"""
        # Determina o canal com base no tipo de entrada
        channel = interaction_or_ctx.channel
        
        # Primeiro deleta a mensagem anterior
        await self.delete_previous_message(channel, tracker)
        
        # Envia nova mensagem
        content = tracker.get_initiative_list()
        
        # Adapta para funcionar com Interaction ou Context
        if isinstance(interaction_or_ctx, discord.Interaction):
            # É uma interação
            if interaction_or_ctx.response.is_done():
                message = await channel.send(content)
            else:
                await interaction_or_ctx.response.send_message(content)
                message = await interaction_or_ctx.original_response()
        else:
            # É um contexto
            message = await interaction_or_ctx.send(content)
        
        # Registra esta mensagem
        tracker.last_message_id = message.id
        self.active_messages[message.id] = channel.id
        
        # Adiciona reações para controle
        for emoji in CONTROL_EMOJIS:
            if emoji == START_COMBAT_EMOJI and tracker.is_active:
                continue
            if emoji == END_COMBAT_EMOJI and not tracker.is_active:
                continue
            await message.add_reaction(emoji)
        
        # Salva o estado do tracker após qualquer modificação
        self.save_tracker(channel.id)
        
        return message
    
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Responde a reações adicionadas às mensagens de iniciativa"""
        # Ignora reações do próprio bot
        if user.bot:
            return
        
        message = reaction.message
        emoji = str(reaction.emoji)
        
        # Verifica se esta é uma mensagem de iniciativa que estamos rastreando
        if message.id not in self.active_messages:
            return
        
        # Obtém o canal e o tracker para esta mensagem
        channel_id = self.active_messages[message.id]
        tracker = self.get_tracker(channel_id)
        
        # Cria um contexto artificial para enviar respostas
        ctx = await self.bot.get_context(message)
        
        # Remove a reação do usuário para manter a interface limpa
        try:
            await message.remove_reaction(emoji, user)
        except discord.HTTPException:
            pass  # Ignora erros de permissão
        
        # Processa a ação com base no emoji
        if emoji == NEXT_TURN_EMOJI:
            # Próximo turno
            next_char = tracker.next_turn()
            if next_char:
                feedback_msg = f"➡️ Agora é o turno de **{next_char.name}**!"
                
                # Se mudou de rodada
                if tracker.current_index == 0:
                    feedback_msg = f"🔄 **Rodada {tracker.round}**\n" + feedback_msg
                    
                await ctx.send(feedback_msg)
                await self.send_initiative_message(ctx, tracker)
            else:
                await ctx.send("❌ Nenhum combate ativo. Use `/init start` ou reaja com ▶️ para iniciar.")
                
        elif emoji == START_COMBAT_EMOJI:
            # Iniciar combate
            if tracker.start_combat():
                current = tracker.current_character()
                await ctx.send(f"⚔️ **Combate iniciado!** Rodada {tracker.round}")
                await self.send_initiative_message(ctx, tracker)
                await ctx.send(f"É o turno de **{current.name}**!")
            else:
                await ctx.send("❌ Não há personagens na iniciativa para iniciar o combate.")
                
        elif emoji == END_COMBAT_EMOJI:
            # Encerrar combate
            if tracker.end_combat():
                await ctx.send("🕊️ **Combate encerrado!**")
                await self.send_initiative_message(ctx, tracker)
            else:
                await ctx.send("❌ Não há combate ativo para encerrar.")
                
        elif emoji == CLEAR_LIST_EMOJI:
            # Limpar lista
            # Pede confirmação
            confirm_msg = await ctx.send("⚠️ Tem certeza que deseja limpar a lista de iniciativa? Reaja com ✅ para confirmar ou ❌ para cancelar.")
            await confirm_msg.add_reaction("✅")
            await confirm_msg.add_reaction("❌")
            
            def check(reaction, user):
                return user != self.bot.user and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == confirm_msg.id
            
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
                
                if str(reaction.emoji) == "✅":
                    tracker.characters = []
                    tracker.is_active = False
                    tracker.current_index = 0
                    tracker.round = 0
                    
                    await ctx.send("🧹 Lista de iniciativa limpa!")
                    await self.send_initiative_message(ctx, tracker)
                else:
                    await ctx.send("Operação cancelada.")
                
                # Remove a mensagem de confirmação
                await confirm_msg.delete()
                
            except asyncio.TimeoutError:
                await ctx.send("Tempo esgotado. Operação cancelada.")
                await confirm_msg.delete()
    
    # Define o grupo de comandos para o bot
    initiative_group = app_commands.Group(name="init", description="Comandos de iniciativa de RPG")
    
    @initiative_group.command(name="show", description="Mostra a lista de iniciativa atual")
    async def initiative(self, interaction: discord.Interaction):
        """Mostra a lista de iniciativa atual"""
        tracker = self.get_tracker(interaction.channel_id)
        await self.send_initiative_message(interaction, tracker)
    
    @initiative_group.command(name="add", description="Adiciona um personagem à iniciativa")
    @app_commands.describe(
        name="Nome do personagem",
        initiative="Valor da iniciativa (número)",
        is_player="Tipo de personagem"
    )
    @app_commands.choices(is_player=[
        app_commands.Choice(name="Jogador (PC)", value="pc"),
        app_commands.Choice(name="NPC/Monstro", value="npc")
    ])
    async def add_character(self, interaction: discord.Interaction, name: str, initiative: int, is_player: str):
        """Adiciona um personagem à iniciativa"""
        tracker = self.get_tracker(interaction.channel_id)
        is_pc = is_player.lower() == "pc"  # Agora is_player já vem como "pc" ou "npc" do Choice
        
        character = Character(name, initiative, is_pc)
        tracker.add_character(character)
        
        # Mensagem diferente baseada no tipo
        tipo_texto = "jogador" if is_pc else "NPC"
        await interaction.response.send_message(f"✅ {name} adicionado à iniciativa como {tipo_texto} com {initiative} pontos.")
        await self.send_initiative_message(interaction, tracker)
    
    @initiative_group.command(name="remove", description="Remove um personagem da iniciativa")
    @app_commands.describe(name="Nome do personagem a ser removido")
    async def remove_character(self, interaction: discord.Interaction, name: str):
        """Remove um personagem da iniciativa"""
        tracker = self.get_tracker(interaction.channel_id)
        
        if tracker.remove_character(name):
            await interaction.response.send_message(f"✅ {name} removido da iniciativa.")
            await self.send_initiative_message(interaction, tracker)
        else:
            await interaction.response.send_message(f"❌ Personagem '{name}' não encontrado.")
    
    @initiative_group.command(name="start", description="Inicia o combate com a iniciativa atual")
    async def start_combat(self, interaction: discord.Interaction):
        """Inicia o combate com a iniciativa atual"""
        tracker = self.get_tracker(interaction.channel_id)
        
        if tracker.start_combat():
            current = tracker.current_character()
            await interaction.response.send_message(f"⚔️ **Combate iniciado!** Rodada {tracker.round}")
            await self.send_initiative_message(interaction, tracker)
            await interaction.followup.send(f"É o turno de **{current.name}**!")
        else:
            await interaction.response.send_message("❌ Não há personagens na iniciativa para iniciar o combate.")
    
    @initiative_group.command(name="end", description="Termina o combate atual")
    async def end_combat(self, interaction: discord.Interaction):
        """Termina o combate atual"""
        tracker = self.get_tracker(interaction.channel_id)
        
        if tracker.end_combat():
            await interaction.response.send_message("🕊️ **Combate encerrado!**")
            await self.send_initiative_message(interaction, tracker)
        else:
            await interaction.response.send_message("❌ Não há combate ativo para encerrar.")
    
    @initiative_group.command(name="next", description="Avança para o próximo turno")
    async def next_turn(self, interaction: discord.Interaction):
        """Avança para o próximo turno"""
        tracker = self.get_tracker(interaction.channel_id)
        
        next_char = tracker.next_turn()
        if next_char:
            message = f"➡️ Agora é o turno de **{next_char.name}**!"
            
            # Se mudou de rodada
            if tracker.current_index == 0:
                message = f"🔄 **Rodada {tracker.round}**\n" + message
                
            await interaction.response.send_message(message)
            await self.send_initiative_message(interaction, tracker)
        else:
            await interaction.response.send_message("❌ Nenhum combate ativo. Use `/init start` para iniciar.")
    
    @initiative_group.command(name="effect", description="Adiciona um efeito a um personagem")
    @app_commands.describe(
        char_name="Nome do personagem",
        effect_name="Nome do efeito",
        duration="Duração em turnos",
        description="Descrição do efeito (opcional)"
    )
    async def add_effect(self, interaction: discord.Interaction, char_name: str, effect_name: str, duration: int, description: str = ""):
        """Adiciona um efeito a um personagem"""
        tracker = self.get_tracker(interaction.channel_id)
        character = tracker.get_character(char_name)
        
        if character:
            effect = Effect(effect_name, duration, description)
            character.add_effect(effect)
            await interaction.response.send_message(f"✨ Efeito **{effect_name}** ({duration} turnos) adicionado a **{char_name}**.")
            await self.send_initiative_message(interaction, tracker)
        else:
            await interaction.response.send_message(f"❌ Personagem '{char_name}' não encontrado.")
    
    @initiative_group.command(name="remove_effect", description="Remove um efeito de um personagem")
    @app_commands.describe(
        char_name="Nome do personagem",
        effect_name="Nome do efeito a ser removido"
    )
    async def remove_effect(self, interaction: discord.Interaction, char_name: str, effect_name: str):
        """Remove um efeito de um personagem"""
        tracker = self.get_tracker(interaction.channel_id)
        character = tracker.get_character(char_name)
        
        if character:
            if character.remove_effect(effect_name):
                await interaction.response.send_message(f"❌ Efeito **{effect_name}** removido de **{char_name}**.")
                await self.send_initiative_message(interaction, tracker)
            else:
                await interaction.response.send_message(f"❌ Efeito '{effect_name}' não encontrado em '{char_name}'.")
        else:
            await interaction.response.send_message(f"❌ Personagem '{char_name}' não encontrado.")
    
    @initiative_group.command(name="clear", description="Limpa toda a lista de iniciativa")
    async def clear_initiative(self, interaction: discord.Interaction):
        """Limpa toda a lista de iniciativa"""
        tracker = self.get_tracker(interaction.channel_id)
        tracker.characters = []
        tracker.is_active = False
        tracker.current_index = 0
        tracker.round = 0
        
        await interaction.response.send_message("🧹 Lista de iniciativa limpa!")
        # Deleta a mensagem anterior se existir
        await self.delete_previous_message(interaction.channel, tracker)
        # Envia uma mensagem vazia (ou poderia não enviar nenhuma)
        await self.send_initiative_message(interaction, tracker)
    
    @initiative_group.command(name="effects", description="Mostra todos os efeitos ativos de um ou todos os personagens")
    @app_commands.describe(char_name="Nome do personagem (opcional, deixe em branco para ver todos)")
    async def show_effects(self, interaction: discord.Interaction, char_name: str = None):
        """Mostra todos os efeitos ativos de um ou todos os personagens"""
        tracker = self.get_tracker(interaction.channel_id)
        
        if not tracker.characters:
            await interaction.response.send_message("❌ Não há personagens na iniciativa.")
            return
        
        embed = discord.Embed(
            title="📊 Efeitos Ativos",
            color=discord.Color.purple()
        )
        
        if char_name:
            # Mostra efeitos de um personagem específico
            character = tracker.get_character(char_name)
            if not character:
                await interaction.response.send_message(f"❌ Personagem '{char_name}' não encontrado.")
                return
                
            if not character.effects:
                embed.description = f"**{character.name}** não possui efeitos ativos."
            else:
                for effect in character.effects:
                    embed.add_field(
                        name=f"{effect.name} ({effect.duration} turnos)",
                        value=effect.description if effect.description else "Sem descrição",
                        inline=False
                    )
                embed.set_footer(text=f"Personagem: {character.name}")
        else:
            # Mostra efeitos de todos os personagens
            has_effects = False
            for character in tracker.characters:
                if character.effects:
                    has_effects = True
                    effects_text = "\n".join([
                        f"• **{effect.name}** ({effect.duration} turnos): {effect.description if effect.description else 'Sem descrição'}"
                        for effect in character.effects
                    ])
                    embed.add_field(
                        name=f"{character.name}",
                        value=effects_text,
                        inline=False
                    )
            
            if not has_effects:
                embed.description = "Nenhum personagem possui efeitos ativos no momento."
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="msg", description="Envia uma mensagem para o canal atual")
    @app_commands.describe(texto="Texto que será enviado no canal")
    async def mensagem(self, interaction: discord.Interaction, texto: str = None):
        """Envia uma mensagem para o canal atual"""
        await interaction.response.send_message(texto if texto else "", ephemeral=True)
        if texto:
            await interaction.channel.send(texto)

    @app_commands.command(name="driscol", description="Grita DRISCOOOOOOL!")
    async def driscol(self, interaction: discord.Interaction):
        await interaction.response.send_message("DRISCOOOOOOL!")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Sincroniza comandos quando o bot entra em um novo servidor"""
        await self.bot.tree.sync(guild=discord.Object(id=guild.id))
        print(f"Comandos sincronizados para o novo servidor: {guild.name}")