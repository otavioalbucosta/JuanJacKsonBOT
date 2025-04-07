
from typing import List
from effects import Effect


class Character:
    def __init__(self, name: str, initiative: int, is_player: bool = False):
        self.name = name
        self.initiative = initiative
        self.is_player = is_player  # Se é jogador ou NPC
        self.effects: List[Effect] = []  # Lista de efeitos ativos
        self.is_active = True  # Se está ativo no combate
    
    def add_effect(self, effect: Effect):
        """Adiciona um efeito ao personagem"""
        self.effects.append(effect)
    
    def remove_effect(self, effect_name: str) -> bool:
        """Remove um efeito específico pelo nome"""
        for effect in self.effects:
            if effect.name.lower() == effect_name.lower():
                self.effects.remove(effect)
                return True
        return False
    
    def update_effects(self) -> List[str]:
        """Atualiza todos os efeitos e retorna os que expiraram"""
        expired = []
        active_effects = []
        
        for effect in self.effects:
            if effect.reduce_duration():
                expired.append(effect.name)
            else:
                active_effects.append(effect)
        
        self.effects = active_effects
        return expired
    
    def __str__(self):
        status = "👤" if self.is_player else "👹"
        effects_str = f" ({', '.join(str(e) for e in self.effects)})" if self.effects else ""
        return f"{status} **{self.name}** - Iniciativa: {self.initiative}{effects_str}"
