import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import datetime
from typing import List, Dict, Optional, Any
from experience.expEntry import ExpEntry


class PlayerExp:
    def __init__(self, name: str):
        self.name = name
        self.entries: List[ExpEntry] = []
    
    def add_exp(self, amount: int, achievement: str) -> ExpEntry:
        entry = ExpEntry(amount, achievement)
        self.entries.append(entry)
        return entry
    
    def remove_exp(self, index: int) -> Optional[ExpEntry]:
        if 0 <= index < len(self.entries):
            return self.entries.pop(index)
        return None
    
    def get_total(self) -> int:
        return sum(entry.amount for entry in self.entries)
    
    def has_entries(self) -> bool:
        return len(self.entries) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'entries': [entry.to_dict() for entry in self.entries]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlayerExp':
        player = cls(data['name'])
        player.entries = [ExpEntry.from_dict(entry) for entry in data['entries']]
        return player