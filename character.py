
from typing import List, Dict, Any
from effects import Effect


class Character:
    def __init__(self, name: str, initiative: int, is_player: bool = False):
        self.name = name
        self.initiative = initiative
        self.is_player = is_player  # Se é jogador ou NPC
        self.effects: List[Effect] = []  # Lista de efeitos ativos
        self.is_active = True  # Se está ativo no combate
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte o personagem para um dicionário para serialização JSON"""
        return {
            'name': self.name,
            'initiative': self.initiative,
            'is_player': self.is_player,
            'effects': [effect.to_dict() for effect in self.effects],
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Character':
        """Cria um personagem a partir de um dicionário"""
        character = cls(data['name'], data['initiative'], data['is_player'])
        character.effects = [Effect.from_dict(effect_data) for effect_data in data['effects']]
        character.is_active = data['is_active']
        return character
    
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