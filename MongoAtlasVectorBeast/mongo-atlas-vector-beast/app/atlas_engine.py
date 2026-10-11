"""
MongoAtlasVectorBeast Execution Engine
Provides low-level MongoDB Atlas vector search, aggregation pipeline compilation,
and chat memory persistence for visual workflow node agents.
"""

import os
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger("vector_beast.engine")

def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class VectorBeastEngine:
    def __init__(self, uri: Optional[str] = None, db_name: str = "vector_beast_db"):
        self.uri = uri or os.environ.get("MONGODB_ATLAS_URI")
        self.db_name = db_name
        self.client = None
        self.db = None
        self.is_atlas = False
        
        # In-memory storage fallback for offline node simulation
        self.mock_documents: List[Dict[str, Any]] = []
        self.mock_memory: Dict[str, List[Dict[str, Any]]] = {}
        
        self._connect()

    def _connect(self):
        if self.uri and self.uri.startswith("mongodb"):
            try:
                from pymongo import MongoClient
                self.client = MongoClient(self.uri, serverSelectionTimeoutMS=2000)
                self.client.admin.command('ping')
                self.db = self.client[self.db_name]
                self.is_atlas = True
                logger.info(f"Connected to Atlas database: {self.db_name}")
                return
            except Exception as e:
                logger.warning(f"Atlas connection fallback: {e}")
        self.is_atlas = False

    def compile_node_pipeline(self, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Compiles an array of visual graph nodes into a MongoDB Atlas Aggregation Pipeline."""
        pipeline = []
        for node in nodes:
            n_type = node.get("type")
            config = node.get("config", {})

            if n_type in ["vectorSearch", "VectorSearchNode"]:
                limit = config.get("limit", 10)
                pipeline.append({
                    "$vectorSearch": {
                        "index": config.get("index", "vector_index"),
                        "path": config.get("field", "embedding"),
                        "queryVector": config.get("queryVector", "[DYNAMIC_EMBEDDING_VECTOR]"),
                        "numCandidates": limit * 5,
                        "limit": limit
                    }
                })
            elif n_type in ["filter", "FilterNode"]:
                op = config.get("op", "eq")
                mongo_op = "$eq" if op == "eq" else f"${op}"
                pipeline.append({
                    "$match": {
                        config.get("field", "status"): {mongo_op: config.get("value", "active")}
                    }
                })
            elif n_type in ["timeSeries", "TimeSeriesNode"]:
                pipeline.append({
                    "$group": {
                        "_id": f"${config.get('groupField', 'sensor_id')}",
                        "avgMetric": {"$avg": f"${config.get('metricField', 'value')}"}
                    }
                })
            elif n_type in ["graphJoin", "GraphJoinNode"]:
                pipeline.append({
                    "$lookup": {
                        "from": config.get("fromCollection", "related_docs"),
                        "localField": config.get("localField", "foreign_key"),
                        "foreignField": config.get("foreignField", "_id"),
                        "as": config.get("asField", "joined_records")
                    }
                })
        return pipeline

    def insert_chat_memory(self, session_id: str, role: str, message: str) -> Dict[str, Any]:
        """Persists chat history into MongoDB Chat Memory collection."""
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
        """Retrieves session chat history."""
        if self.is_atlas and self.db is not None:
            return list(self.db.chat_memory_sessions.find({"session_id": session_id}, {"_id": 0}).sort("timestamp", -1).limit(limit))
        return self.mock_memory.get(session_id, [])[-limit:]
