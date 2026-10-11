"""
TalentSignal ADK Function Tools — Swarm Management, Topology Compilation, & Session Memory
"""

from typing import Dict, Any, List
from app.personas import TALENTSIGNAL_SWARM_PERSONAS
from app.node_agents import TALENTSIGNAL_NODE_AGENTS
from app.compiler import compile_workflow_graph
from app.atlas_client import TalentSignalAtlasClient

atlas = TalentSignalAtlasClient()

def list_talentsignal_swarm_personas() -> List[Dict[str, Any]]:
    """Lists all 8 specialized TalentSignal Agent Swarm personas."""
    return TALENTSIGNAL_SWARM_PERSONAS

def list_talentsignal_canvas_node_agents() -> List[Dict[str, Any]]:
    """Lists all modular TalentSignal canvas node agents."""
    return TALENTSIGNAL_NODE_AGENTS

def compile_talentsignal_topology(workflow_graph: Dict[str, Any]) -> Dict[str, Any]:
    """Compiles a visual TalentSignal topology graph into an executable MongoDB Atlas vector pipeline."""
    return compile_workflow_graph(workflow_graph)

def record_talentsignal_session(session_id: str, role: str, message: str) -> Dict[str, Any]:
    """Persists a conversation turn in TalentSignal MongoDB Chat Memory."""
    doc = atlas.insert_chat_memory(session_id, role, message)
    return {"status": "persisted", "record": doc}

def fetch_talentsignal_session(session_id: str, limit: int = 10) -> Dict[str, Any]:
    """Retrieves session chat history from TalentSignal MongoDB Chat Memory."""
    history = atlas.get_chat_memory(session_id, limit)
    return {"session_id": session_id, "count": len(history), "history": history}
