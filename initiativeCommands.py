import asyncio
import discord
from discord.ext import commands
from typing import Dict
from initiativeQueue import InitiativeTracker
from character import Character
from effects import Effect
import pickle
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
TRACKER_FILE = "initiative_tracker_{}.pkl"

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
        """Salva o estado do tracker para um canal específico"""
        tracker = self.trackers.get(channel_id)
        if tracker:
            filepath = os.path.join(DATA_DIR, TRACKER_FILE.format(channel_id))
            try:
                with open(filepath, 'wb') as f:
                    # Removemos a referência ao last_message_id antes de salvar
                    # porque pode mudar entre sessões
                    temp_message_id = tracker.last_message_id
                    tracker.last_message_id = None
                    pickle.dump(tracker, f)
                    tracker.last_message_id = temp_message_id
                print(f"Tracker para o canal {channel_id} salvo com sucesso!")
            except Exception as e:
                print(f"Erro ao salvar tracker para o canal {channel_id}: {e}")
    
    def load_tracker(self, channel_id: int) -> bool:
        """Carrega o estado do tracker para um canal específico"""
        filepath = os.path.join(DATA_DIR, TRACKER_FILE.format(channel_id))
        if os.path.exists(filepath):
            try:
                with open(filepath, 'rb') as f:
                    self.trackers[channel_id] = pickle.load(f)
                print(f"Tracker para o canal {channel_id} carregado com sucesso!")
                return True
            except Exception as e:
                print(f"Erro ao carregar tracker para o canal {channel_id}: {e}")
        return False
    
    def load_all_trackers(self):
        """Carrega todos os trackers salvos"""
        if os.path.exists(DATA_DIR):
            for filename in os.listdir(DATA_DIR):
                if filename.startswith("initiative_tracker_") and filename.endswith(".pkl"):
                    try:
                        channel_id = int(filename.replace("initiative_tracker_", "").replace(".pkl", ""))
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
    
    async def send_initiative_message(self, ctx, tracker):
        """Envia uma nova mensagem de iniciativa com reações após deletar a antiga"""
        # Primeiro deleta a mensagem anterior
        await self.delete_previous_message(ctx.channel, tracker)
        
        # Envia nova mensagem
        content = tracker.get_initiative_list()
        message = await ctx.send(content)
        
        # Registra esta mensagem
        tracker.last_message_id = message.id
        self.active_messages[message.id] = ctx.channel.id
        
        # Adiciona reações para controle
        for emoji in CONTROL_EMOJIS:
            await message.add_reaction(emoji)
        
        # Salva o estado do tracker após qualquer modificação
        self.save_tracker(ctx.channel.id)
        
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
                await ctx.send("❌ Nenhum combate ativo. Use `$init start` ou reaja com ▶️ para iniciar.")
                
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
    
    @commands.group(name="init", invoke_without_command=True)
    async def initiative(self, ctx):
        """Mostra a lista de iniciativa atual"""
        tracker = self.get_tracker(ctx.channel.id)
        await self.send_initiative_message(ctx, tracker)
    
    @initiative.command(name="add")
    async def add_character(self, ctx, name: str, initiative: int, is_player: str = "npc"):
        """Adiciona um personagem à iniciativa
        Exemplo: $init add "Goblin Arqueiro" 15 npc"""
        tracker = self.get_tracker(ctx.channel.id)
        is_pc = is_player.lower() in ["player", "pc", "jogador"]
        
        character = Character(name, initiative, is_pc)
        tracker.add_character(character)
        
        await ctx.send(f"✅ {name} adicionado à iniciativa com {initiative} pontos.")
        await self.send_initiative_message(ctx, tracker)
    
    @initiative.command(name="remove", aliases=["rm"])
    async def remove_character(self, ctx, *, name: str):
        """Remove um personagem da iniciativa
        Exemplo: $init remove "Goblin Arqueiro" """
        tracker = self.get_tracker(ctx.channel.id)
        
        if tracker.remove_character(name):
            await ctx.send(f"✅ {name} removido da iniciativa.")
            await self.send_initiative_message(ctx, tracker)
        else:
            await ctx.send(f"❌ Personagem '{name}' não encontrado.")
    
    @initiative.command(name="start")
    async def start_combat(self, ctx):
        """Inicia o combate com a iniciativa atual"""
        tracker = self.get_tracker(ctx.channel.id)
        
        if tracker.start_combat():
            current = tracker.current_character()
            await ctx.send(f"⚔️ **Combate iniciado!** Rodada {tracker.round}")
            await self.send_initiative_message(ctx, tracker)
            await ctx.send(f"É o turno de **{current.name}**!")
        else:
            await ctx.send("❌ Não há personagens na iniciativa para iniciar o combate.")
    
    @initiative.command(name="end")
    async def end_combat(self, ctx):
        """Termina o combate atual"""
        tracker = self.get_tracker(ctx.channel.id)
        
        if tracker.end_combat():
            await ctx.send("🕊️ **Combate encerrado!**")
            await self.send_initiative_message(ctx, tracker)
        else:
            await ctx.send("❌ Não há combate ativo para encerrar.")
    
    @initiative.command(name="next", aliases=["n"])
    async def next_turn(self, ctx):
        """Avança para o próximo turno"""
        tracker = self.get_tracker(ctx.channel.id)
        
        next_char = tracker.next_turn()
        if next_char:
            message = f"➡️ Agora é o turno de **{next_char.name}**!"
            
            # Se mudou de rodada
            if tracker.current_index == 0:
                message = f"🔄 **Rodada {tracker.round}**\n" + message
                
            await ctx.send(message)
            await self.send_initiative_message(ctx, tracker)
        else:
            await ctx.send("❌ Nenhum combate ativo. Use `$init start` para iniciar.")
    
    @initiative.command(name="effect", aliases=["ef"])
    async def add_effect(self, ctx, char_name: str, effect_name: str, duration: int, *, description: str = ""):
        """Adiciona um efeito a um personagem
        Exemplo: $init effect "Goblin" "Atordoado" 2 "Não pode agir"
        """
        tracker = self.get_tracker(ctx.channel.id)
        character = tracker.get_character(char_name)
        
        if character:
            effect = Effect(effect_name, duration, description)
            character.add_effect(effect)
            await ctx.send(f"✨ Efeito **{effect_name}** ({duration} turnos) adicionado a **{char_name}**.")
            await self.send_initiative_message(ctx, tracker)
        else:
            await ctx.send(f"❌ Personagem '{char_name}' não encontrado.")
    
    @initiative.command(name="remove_effect", aliases=["rmef"])
    async def remove_effect(self, ctx, char_name: str, effect_name: str):
        """Remove um efeito de um personagem
        Exemplo: $init rmef "Goblin" "Atordoado"
        """
        tracker = self.get_tracker(ctx.channel.id)
        character = tracker.get_character(char_name)
        
        if character:
            if character.remove_effect(effect_name):
                await ctx.send(f"❌ Efeito **{effect_name}** removido de **{char_name}**.")
                await self.send_initiative_message(ctx, tracker)
            else:
                await ctx.send(f"❌ Efeito '{effect_name}' não encontrado em '{char_name}'.")
        else:
            await ctx.send(f"❌ Personagem '{char_name}' não encontrado.")
    
    @initiative.command(name="clear")
    async def clear_initiative(self, ctx):
        """Limpa toda a lista de iniciativa"""
        tracker = self.get_tracker(ctx.channel.id)
        tracker.characters = []
        tracker.is_active = False
        tracker.current_index = 0
        tracker.round = 0
        
        await ctx.send("🧹 Lista de iniciativa limpa!")
        # Deleta a mensagem anterior se existir
        await self.delete_previous_message(ctx.channel, tracker)
        # Envia uma mensagem vazia (ou poderia não enviar nenhuma)
        await self.send_initiative_message(ctx, tracker)
    
    @initiative.command(name="effects", aliases=["efs"])
    async def show_effects(self, ctx, *, char_name: str = None):
        """Mostra todos os efeitos ativos de um ou todos os personagens
        Exemplo: $init effects "Goblin" ou $init effects para todos
        """
        tracker = self.get_tracker(ctx.channel.id)
        
        if not tracker.characters:
            await ctx.send("❌ Não há personagens na iniciativa.")
            return
        
        embed = discord.Embed(
            title="📊 Efeitos Ativos",
            color=discord.Color.purple()
        )
        
        if char_name:
            # Mostra efeitos de um personagem específico
            character = tracker.get_character(char_name)
            if not character:
                await ctx.send(f"❌ Personagem '{char_name}' não encontrado.")
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
        
        await ctx.send(embed=embed)
