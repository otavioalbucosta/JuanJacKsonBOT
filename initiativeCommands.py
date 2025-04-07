from discord.ext import commands
from dotenv import load_dotenv
from typing import Dict
from initiativeQueue import InitiativeTracker
from character import Character
from effects import Effect


class InitiativeCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.trackers: Dict[int, InitiativeTracker] = {}  # Um tracker por canal
    
    def get_tracker(self, channel_id: int) -> InitiativeTracker:
        """Obtém (ou cria) um tracker para o canal específico"""
        if channel_id not in self.trackers:
            self.trackers[channel_id] = InitiativeTracker()
        return self.trackers[channel_id]
    
    @commands.group(name="init", invoke_without_command=True)
    async def initiative(self, ctx):
        """Mostra a lista de iniciativa atual"""
        tracker = self.get_tracker(ctx.channel.id)
        await ctx.send(tracker.get_initiative_list())
    
    @initiative.command(name="add")
    async def add_character(self, ctx, name: str, initiative: int, is_player: str = "npc"):
        """Adiciona um personagem à iniciativa
        Exemplo: $init add "Goblin Arqueiro" 15 npc"""
        tracker = self.get_tracker(ctx.channel.id)
        is_pc = is_player.lower() in ["player", "pc", "jogador"]
        
        character = Character(name, initiative, is_pc)
        tracker.add_character(character)
        
        await ctx.send(f"✅ {name} adicionado à iniciativa com {initiative} pontos.")
        await ctx.send(tracker.get_initiative_list())
    
    @initiative.command(name="remove", aliases=["rm"])
    async def remove_character(self, ctx, *, name: str):
        """Remove um personagem da iniciativa
        Exemplo: $init remove "Goblin Arqueiro" """
        tracker = self.get_tracker(ctx.channel.id)
        
        if tracker.remove_character(name):
            await ctx.send(f"✅ {name} removido da iniciativa.")
            await ctx.send(tracker.get_initiative_list())
        else:
            await ctx.send(f"❌ Personagem '{name}' não encontrado.")
    
    @initiative.command(name="start")
    async def start_combat(self, ctx):
        """Inicia o combate com a iniciativa atual"""
        tracker = self.get_tracker(ctx.channel.id)
        
        if tracker.start_combat():
            current = tracker.current_character()
            await ctx.send(f"⚔️ **Combate iniciado!** Rodada {tracker.round}")
            await ctx.send(tracker.get_initiative_list())
            await ctx.send(f"É o turno de **{current.name}**!")
        else:
            await ctx.send("❌ Não há personagens na iniciativa para iniciar o combate.")
    
    @initiative.command(name="end")
    async def end_combat(self, ctx):
        """Termina o combate atual"""
        tracker = self.get_tracker(ctx.channel.id)
        
        if tracker.end_combat():
            await ctx.send("🕊️ **Combate encerrado!**")
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
            await ctx.send(tracker.get_initiative_list())
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
            await ctx.send(tracker.get_initiative_list())
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
                await ctx.send(tracker.get_initiative_list())
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