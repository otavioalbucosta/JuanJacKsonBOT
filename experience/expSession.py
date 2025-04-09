import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import datetime
from typing import List, Dict, Optional, Any
from experience.expEntry import *
from experience.playerExp import *

class ExpSession:
    def __init__(self):
        self.party_entries: List[ExpEntry] = []
        self.players: Dict[str, PlayerExp] = {}
        self.creation_date = datetime.datetime.now().isoformat()
        self.session_name = None
        self.is_finalized = False
    
    def add_party_exp(self, amount: int, achievement: str) -> ExpEntry:
        entry = ExpEntry(amount, achievement)
        self.party_entries.append(entry)
        return entry
    
    def remove_party_exp(self, index: int) -> Optional[ExpEntry]:
        if 0 <= index < len(self.party_entries):
            return self.party_entries.pop(index)
        return None
    
    def add_player_exp(self, character_name: str, amount: int, achievement: str) -> ExpEntry:
        if character_name not in self.players:
            self.players[character_name] = PlayerExp(character_name)
        return self.players[character_name].add_exp(amount, achievement)
    
    def remove_player_exp(self, character_name: str, index: int) -> Optional[ExpEntry]:
        if character_name in self.players:
            entry = self.players[character_name].remove_exp(index)
            # Remove o player se não tiver mais entradas
            if not self.players[character_name].has_entries():
                del self.players[character_name]
            return entry
        return None
    
    def get_party_total(self) -> int:
        return sum(entry.amount for entry in self.party_entries)
    
    def get_player_totals(self) -> Dict[str, int]:
        return {name: player.get_total() for name, player in self.players.items()}
    
    def get_grand_totals(self) -> Dict[str, int]:
        party_total = self.get_party_total()
        result = {}
        for name, player in self.players.items():
            result[name] = player.get_total() + party_total
        return result
    
    def finalize(self, session_name: str):
        self.session_name = session_name
        self.is_finalized = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'party_entries': [entry.to_dict() for entry in self.party_entries],
            'players': {name: player.to_dict() for name, player in self.players.items()},
            'creation_date': self.creation_date,
            'session_name': self.session_name,
            'is_finalized': self.is_finalized
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExpSession':
        session = cls()
        session.party_entries = [ExpEntry.from_dict(entry) for entry in data['party_entries']]
        session.players = {name: PlayerExp.from_dict(player_data) for name, player_data in data['players'].items()}
        session.creation_date = data['creation_date']
        session.session_name = data['session_name']
        session.is_finalized = data['is_finalized']
        return session