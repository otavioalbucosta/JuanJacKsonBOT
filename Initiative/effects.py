import datetime
from typing import Dict, Any

class Effect:
    def __init__(self, name: str, duration: int, description: str = ""):
        self.name = name
        self.duration = duration  # duração em turnos
        self.description = description
        self.created_at = datetime.datetime.now().isoformat()  # Salva como string ISO
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte o efeito para um dicionário para serialização JSON"""
        return {
            'name': self.name,
            'duration': self.duration,
            'description': self.description,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Effect':
        """Cria um efeito a partir de um dicionário"""
        effect = cls(data['name'], data['duration'], data['description'])
        effect.created_at = data['created_at']
        return effect
    
    def reduce_duration(self):
        """Reduz a duração do efeito em 1 turno"""
        self.duration -= 1
        return self.duration <= 0  # Retorna True se o efeito expirou
    
    def __str__(self):
        return f"{self.name} ({self.duration} turnos)"