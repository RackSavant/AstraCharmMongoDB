"""
ADK Function Tools for MongoAtlasVectorBeast Node Agents
Provides functions to list available node agents, compile graph canvas workflows,
and run node executions.
"""

from typing import Dict, Any, List, Optional
from app.node_agents import NODE_AGENTS_CATALOG, get_node_agent_by_id
from app.atlas_engine import VectorBeastEngine

engine = VectorBeastEngine()

def list_canvas_node_agents() -> List[Dict[str, Any]]:
    """Lists all available modular node agents ready to be wired on visual canvas or turned into n8n nodes."""
    return NODE_AGENTS_CATALOG

def compile_canvas_graph_pipeline(workflow_graph: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compiles a visual graph of node agents into an executable MongoDB Atlas aggregation pipeline.
    Demonstrates topology compilation (node ordering determines pre vs post filter pipeline stages).
    """
    nodes = workflow_graph.get("nodes", [])
    pipeline = engine.compile_node_pipeline(nodes)
    return {
        "status": "success",
        "nodes_count": len(nodes),
        "compiled_pipeline": pipeline
    }

def record_session_memory(session_id: str, role: str, message: str) -> Dict[str, Any]:
    """Persists a conversation turn into MongoDB Chat Memory."""
    doc = engine.insert_chat_memory(session_id, role, message)
    return {
        "status": "persisted",
        "record": doc
    }

def fetch_session_memory(session_id: str, limit: int = 10) -> Dict[str, Any]:
    """Retrieves session chat history from MongoDB Chat Memory."""
    history = engine.get_chat_memory(session_id, limit)
    return {
        "session_id": session_id,
        "count": len(history),
        "history": history
    }
