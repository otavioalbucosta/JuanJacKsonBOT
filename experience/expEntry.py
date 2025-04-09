import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import datetime
from typing import List, Dict, Optional, Any

class ExpEntry:
    def __init__(self, amount: int, achievement: str):
        self.amount = amount
        self.achievement = achievement
        self.timestamp = datetime.datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'amount': self.amount,
            'achievement': self.achievement,
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExpEntry':
        entry = cls(data['amount'], data['achievement'])
        entry.timestamp = data['timestamp']
        return entry