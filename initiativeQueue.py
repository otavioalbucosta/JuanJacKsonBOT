
from character import Character
from typing import List, Optional

class InitiativeTracker:
    def __init__(self):
        self.characters: List[Character] = []
        self.current_index = 0
        self.round = 0
        self.is_active = False
    
    def add_character(self, character: Character):
        """Adiciona um personagem à iniciativa e reordena a lista"""
        self.characters.append(character)
        # Ordenar personagens por iniciativa (decrescente)
        self.characters.sort(key=lambda x: x.initiative, reverse=True)
    
    def remove_character(self, name: str) -> bool:
        """Remove um personagem da iniciativa"""
        for i, char in enumerate(self.characters):
            if char.name.lower() == name.lower():
                # Ajusta o índice atual se necessário
                if i <= self.current_index and self.current_index > 0:
                    self.current_index -= 1
                self.characters.pop(i)
                return True
        return False
    
    def get_character(self, name: str) -> Optional[Character]:
        """Busca um personagem pelo nome"""
        for char in self.characters:
            if char.name.lower() == name.lower():
                return char
        return None
    
    def start_combat(self):
        """Inicia o combate"""
        if not self.characters:
            return False
        
        self.is_active = True
        self.current_index = 0
        self.round = 1
        return True
    
    def end_combat(self):
        """Finaliza o combate"""
        self.is_active = False
        self.current_index = 0
        self.round = 0
        return True
    
    def next_turn(self) -> Optional[Character]:
        """Avança para o próximo personagem na iniciativa"""
        if not self.is_active or not self.characters:
            return None
            
        # Avança para o próximo personagem
        self.current_index += 1
        
        # Se chegou ao final da lista, volta ao início e incrementa o round
        if self.current_index >= len(self.characters):
            self.current_index = 0
            self.round += 1
            
        return self.current_character()
    
    def current_character(self) -> Optional[Character]:
        """Retorna o personagem atual"""
        if not self.is_active or not self.characters:
            return None
            
        if 0 <= self.current_index < len(self.characters):
            char = self.characters[self.current_index]
            
            # Processa efeitos no início do turno do personagem
            expired = char.update_effects()
            
            return char
        return None
    
    def get_initiative_list(self) -> str:
        """Retorna a lista de iniciativa formatada"""
        if not self.characters:
            return "Nenhum personagem na iniciativa."
            
        result = []
        for i, char in enumerate(self.characters):
            prefix = "➡️ " if i == self.current_index and self.is_active else "   "
            result.append(f"{prefix}{char}")
            
        header = f"📋 **INICIATIVA** (Rodada {self.round})\n" if self.is_active else "📋 **INICIATIVA**\n"
        return header + "\n".join(result)