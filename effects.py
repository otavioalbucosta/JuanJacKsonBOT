import datetime

class Effect:
    def __init__(self, name: str, duration: int, description: str = ""):
        self.name = name
        self.duration = duration  # duração em turnos
        self.description = description
        self.created_at = datetime.datetime.now()
    
    def reduce_duration(self):
        """Reduz a duração do efeito em 1 turno"""
        self.duration -= 1
        return self.duration <= 0  # Retorna True se o efeito expirou
    
    def __str__(self):
        return f"{self.name} ({self.duration} turnos)"