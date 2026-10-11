"""
ADK Function Tools for n8n MongoDB Integration
Exposes n8n workflow generation, validation, and execution helpers to Agents CLI.
"""

from typing import Dict, Any, List, Optional
from app.n8n_adapter import N8nMongoDBAdapter

adapter = N8nMongoDBAdapter()

def generate_n8n_mongodb_agent_workflow(
    agent_name: str,
    system_prompt: str,
    database_name: str = "agentbook_db",
    collection_name: str = "knowledge_embeddings",
    index_name: str = "vector_index"
) -> Dict[str, Any]:
    """
    Generates a ready-to-import n8n workflow JSON containing AI Agent + MongoDB Vector Store Tool + MongoDB Chat Memory.
    """
    workflow = adapter.generate_ai_agent_workflow(
        agent_name=agent_name,
        system_prompt=system_prompt,
        database_name=database_name,
        collection_name=collection_name,
        index_name=index_name
    )
    errors = adapter.validate_n8n_workflow(workflow)
    return {
        "valid": len(errors) == 0,
        "validation_errors": errors,
        "workflow": workflow
    }

def validate_n8n_workflow_json(workflow_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates an n8n workflow JSON structure for MongoDB credentials, nodes, and connection bindings.
    """
    errors = adapter.validate_n8n_workflow(workflow_json)
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
