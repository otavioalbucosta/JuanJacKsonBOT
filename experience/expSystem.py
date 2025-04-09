import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import datetime
from typing import List, Dict, Optional, Any
from experience.expSession import *
from experience.expEntry import *

class ExpSystem:
    def __init__(self, data_dir: str = "bot_data"):
        self.data_dir = data_dir
        # O histórico agora é um dicionário vazio que será preenchido por servidor
        self.history: Dict[int, Dict[str, ExpSession]] = {}
        self.active_sessions: Dict[int, ExpSession] = {}
        
        # Criar diretório se não existir
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
    
    def _get_history_file(self, guild_id: int) -> str:
        """Retorna o caminho do arquivo de histórico específico do servidor"""
        return os.path.join(self.data_dir, f"exp_history_{guild_id}.json")
    
    def _get_active_session_file(self, guild_id: int) -> str:
        """Retorna o caminho do arquivo de sessão ativa específico do servidor"""
        return os.path.join(self.data_dir, f"active_exp_session_{guild_id}.json")
    
    def get_active_session(self, guild_id: int) -> ExpSession:
        """Obtém a sessão ativa para um servidor específico"""
        if guild_id not in self.active_sessions:
            self.active_sessions[guild_id] = ExpSession()
            self.load_active_session(guild_id)
        return self.active_sessions[guild_id]
    
    def get_history(self, guild_id: int) -> Dict[str, ExpSession]:
        """Obtém o histórico para um servidor específico"""
        if guild_id not in self.history:
            self.history[guild_id] = {}
            self.load_history(guild_id)
        return self.history[guild_id]
    
    def create_session(self, guild_id: int) -> ExpSession:
        """Cria uma nova sessão de experiência para um servidor específico"""
        self.active_sessions[guild_id] = ExpSession()
        self.save_active_session(guild_id)
        return self.active_sessions[guild_id]
        
    def clear_active_session(self, guild_id: int) -> bool:
        """Limpa a sessão ativa de um servidor específico"""
        if guild_id in self.active_sessions:
            self.active_sessions[guild_id] = ExpSession()
            self.save_active_session(guild_id)
            return True
        return False
    
    def add_party_exp(self, guild_id: int, amount: int, achievement: str) -> ExpEntry:
        """Adiciona experiência para o grupo em um servidor específico"""
        active_session = self.get_active_session(guild_id)
        entry = active_session.add_party_exp(amount, achievement)
        self.save_active_session(guild_id)
        return entry
    
    def remove_party_exp(self, guild_id: int, index: int) -> Optional[ExpEntry]:
        """Remove uma entrada de experiência do grupo em um servidor específico"""
        active_session = self.get_active_session(guild_id)
        entry = active_session.remove_party_exp(index)
        self.save_active_session(guild_id)
        return entry
    
    def add_player_exp(self, guild_id: int, character_name: str, amount: int, achievement: str) -> ExpEntry:
        """Adiciona experiência para um jogador específico em um servidor específico"""
        active_session = self.get_active_session(guild_id)
        entry = active_session.add_player_exp(character_name, amount, achievement)
        self.save_active_session(guild_id)
        return entry
    
    def remove_player_exp(self, guild_id: int, character_name: str, index: int) -> Optional[ExpEntry]:
        """Remove uma entrada de experiência de um jogador em um servidor específico"""
        active_session = self.get_active_session(guild_id)
        entry = active_session.remove_player_exp(character_name, index)
        self.save_active_session(guild_id)
        return entry
    
    def finalize_session(self, guild_id: int, session_name: str) -> bool:
        """Finaliza a sessão atual e move para o histórico de um servidor específico"""
        active_session = self.get_active_session(guild_id)
        if not active_session.party_entries and not active_session.players:
            return False  # Sessão vazia
        
        # Obtém o histórico do servidor
        server_history = self.get_history(guild_id)
        
        # Verificar se o nome já existe
        if session_name in server_history:
            return False
        
        active_session.finalize(session_name)
        server_history[session_name] = active_session
        self.save_history(guild_id)
        
        # Criar nova sessão ativa
        self.active_sessions[guild_id] = ExpSession()
        self.save_active_session(guild_id)
        
        return True
    
    def get_session_by_name(self, guild_id: int, session_name: str) -> Optional[ExpSession]:
        """Obtém uma sessão pelo nome em um servidor específico"""
        server_history = self.get_history(guild_id)
        return server_history.get(session_name)
    
    def get_all_session_names(self, guild_id: int) -> List[str]:
        """Obtém todos os nomes de sessões no histórico de um servidor específico"""
        server_history = self.get_history(guild_id)
        return list(server_history.keys())
    
    def save_active_session(self, guild_id: int):
        """Salva a sessão ativa em arquivo para um servidor específico"""
        active_session = self.get_active_session(guild_id)
        with open(self._get_active_session_file(guild_id), 'w', encoding='utf-8') as f:
            json.dump(active_session.to_dict(), f, ensure_ascii=False, indent=2)
    
    def load_active_session(self, guild_id: int) -> bool:
        """Carrega a sessão ativa do arquivo para um servidor específico"""
        file_path = self._get_active_session_file(guild_id)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.active_sessions[guild_id] = ExpSession.from_dict(data)
                return True
            except Exception as e:
                print(f"Erro ao carregar sessão ativa para servidor {guild_id}: {e}")
        return False
    
    def save_history(self, guild_id: int):
        """Salva o histórico em arquivo para um servidor específico"""
        server_history = self.get_history(guild_id)
        with open(self._get_history_file(guild_id), 'w', encoding='utf-8') as f:
            history_dict = {name: session.to_dict() for name, session in server_history.items()}
            json.dump(history_dict, f, ensure_ascii=False, indent=2)
    
    def load_history(self, guild_id: int) -> bool:
        """Carrega o histórico do arquivo para um servidor específico"""
        file_path = self._get_history_file(guild_id)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.history[guild_id] = {name: ExpSession.from_dict(session_data) for name, session_data in data.items()}
                return True
            except Exception as e:
                print(f"Erro ao carregar histórico para servidor {guild_id}: {e}")
        return False