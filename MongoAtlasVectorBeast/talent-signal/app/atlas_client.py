"""
TalentSignal MongoDB Atlas Client — Handles Vector Search, Chat Memory, and Candidate Swarm Profiles
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from app.personas import TALENTSIGNAL_SWARM_PERSONAS

logger = logging.getLogger("talentsignal.atlas")

def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class TalentSignalAtlasClient:
    def __init__(self, uri: Optional[str] = None, db_name: str = "talentsignal_db"):
        self.uri = uri or os.environ.get("MONGODB_ATLAS_URI")
        self.db_name = db_name
        self.client = None
        self.db = None
        self.is_atlas = False
        
        self.mock_profiles: Dict[str, Dict[str, Any]] = {}
        self.mock_memory: Dict[str, List[Dict[str, Any]]] = {}
        
        self._connect()
        self._seed_personas()

    def _connect(self):
        if self.uri and self.uri.startswith("mongodb"):
            try:
                from pymongo import MongoClient
                self.client = MongoClient(self.uri, serverSelectionTimeoutMS=2000)
                self.client.admin.command('ping')
                self.db = self.client[self.db_name]
                self.is_atlas = True
                logger.info(f"Connected to TalentSignal Atlas database: {self.db_name}")
                return
            except Exception as e:
                logger.warning(f"TalentSignal Atlas connection fallback: {e}")
        self.is_atlas = False

    def _seed_personas(self):
        for persona in TALENTSIGNAL_SWARM_PERSONAS:
            self.mock_profiles[persona["agent_id"]] = persona

    def get_swarm_personas(self) -> List[Dict[str, Any]]:
        return list(self.mock_profiles.values())

    def insert_chat_memory(self, session_id: str, role: str, message: str) -> Dict[str, Any]:
        doc = {
            "session_id": session_id,
            "role": role,
            "message": message,
            "timestamp": _utc_now_iso()
        }
        if self.is_atlas and self.db is not None:
            self.db.chat_memory_sessions.insert_one(doc)
        else:
            if session_id not in self.mock_memory:
                self.mock_memory[session_id] = []
            self.mock_memory[session_id].append(doc)
        return doc

    def get_chat_memory(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        if self.is_atlas and self.db is not None:
            return list(self.db.chat_memory_sessions.find({"session_id": session_id}, {"_id": 0}).sort("timestamp", -1).limit(limit))
        return self.mock_memory.get(session_id, [])[-limit:]
