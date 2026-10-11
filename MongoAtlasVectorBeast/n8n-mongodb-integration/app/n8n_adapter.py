"""
n8n MongoDB Integration Adapter
Provides helper tools to build, validate, and trigger n8n workflows integrated with MongoDB Atlas,
MongoDB Vector Store, and MongoDB Chat Memory.
"""

import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("n8n_mongodb_integration")

class N8nMongoDBAdapter:
    def __init__(self, n8n_host: Optional[str] = None):
        self.n8n_host = n8n_host or "http://localhost:5678"

    def validate_n8n_workflow(self, workflow_data: Dict[str, Any]) -> List[str]:
        """Validates n8n workflow schema, checking nodes, types, and connection bindings."""
        errors = []
        if not isinstance(workflow_data, dict):
            return ["Workflow payload must be a JSON object."]

        nodes = workflow_data.get("nodes", [])
        if not nodes:
            errors.append("Workflow must contain at least one node.")

        node_ids = set()
        node_names = set()

        for node in nodes:
            n_id = node.get("id")
            n_name = node.get("name")
            n_type = node.get("type", "")

            if not n_id or n_id in node_ids:
                errors.append(f"Invalid or duplicate node ID: {n_id}")
            node_ids.add(n_id)

            if not n_name or n_name in node_names:
                errors.append(f"Invalid or duplicate node name: {n_name}")
            node_names.add(n_name)

            # Check MongoDB specific nodes
            if "mongoDb" in n_type and "credentials" not in node:
                errors.append(f"Node '{n_name}' ({n_type}) requires 'credentials.mongoDb' configuration.")

        connections = workflow_data.get("connections", {})
        for source_name, conn_data in connections.items():
            if source_name not in node_names:
                errors.append(f"Connection references unknown source node: {source_name}")

        return errors

    def generate_ai_agent_workflow(
        self,
        agent_name: str,
        system_prompt: str,
        database_name: str = "agentbook_db",
        collection_name: str = "knowledge_embeddings",
        index_name: str = "vector_index"
    ) -> Dict[str, Any]:
        """Generates a complete n8n workflow JSON with AI Agent + MongoDB Vector Store + MongoDB Chat Memory."""
        workflow = {
            "name": f"n8n AI Agent — {agent_name}",
            "nodes": [
                {
                  "parameters": {
                    "httpMethod": "POST",
                    "path": f"agent-{agent_name.lower().replace(' ', '-')}",
                    "responseMode": "lastNode"
                  },
                  "id": "node-webhook-1",
                  "name": "Webhook Trigger",
                  "type": "n8n-nodes-base.webhook",
                  "typeVersion": 1,
                  "position": [100, 300]
                },
                {
                  "parameters": {
                    "agent": "conversationalAgent",
                    "promptType": "define",
                    "text": "={{ $json.body.message }}",
                    "options": {
                      "systemMessage": system_prompt
                    }
                  },
                  "id": "node-ai-agent-2",
                  "name": "AI Agent Node",
                  "type": "@n8n/n8n-nodes-langchain.agent",
                  "typeVersion": 1.7,
                  "position": [350, 300]
                },
                {
                  "parameters": {
                    "modelName": "models/gemini-2.5-flash"
                  },
                  "id": "node-llm-3",
                  "name": "Google Gemini Model",
                  "type": "@n8n/n8n-nodes-langchain.lmChatGoogleGemini",
                  "typeVersion": 1,
                  "position": [200, 520],
                  "credentials": {
                    "googlePalmApi": {
                      "id": "cred-gemini-1",
                      "name": "Gemini API Key"
                    }
                  }
                },
                {
                  "parameters": {
                    "mode": "retrieve-as-tool",
                    "toolName": "mongodb_vector_search",
                    "toolDescription": "Perform vector similarity search on MongoDB Atlas knowledge embeddings.",
                    "options": {
                      "indexName": index_name,
                      "collectionName": collection_name,
                      "databaseName": database_name
                    }
                  },
                  "id": "node-vector-store-4",
                  "name": "MongoDB Atlas Vector Store Node",
                  "type": "@n8n/n8n-nodes-langchain.vectorStoreMongoDbAtlas",
                  "typeVersion": 1,
                  "position": [500, 520],
                  "credentials": {
                    "mongoDb": {
                      "id": "cred-mongodb-1",
                      "name": "MongoDB Connection"
                    }
                  }
                },
                {
                  "parameters": {
                    "collectionName": "chat_memory_sessions",
                    "sessionKey": "={{ $json.body.sessionId || 'default' }}",
                    "databaseName": database_name
                  },
                  "id": "node-chat-memory-5",
                  "name": "MongoDB Chat Memory Node",
                  "type": "@n8n/n8n-nodes-langchain.memoryMongoDbChat",
                  "typeVersion": 1,
                  "position": [350, 520],
                  "credentials": {
                    "mongoDb": {
                      "id": "cred-mongodb-1",
                      "name": "MongoDB Connection"
                    }
                  }
                }
            ],
            "connections": {
                "Webhook Trigger": {
                  "main": [[{"node": "AI Agent Node", "type": "main", "index": 0}]]
                },
                "Google Gemini Model": {
                  "ai_languageModel": [[{"node": "AI Agent Node", "type": "ai_languageModel", "index": 0}]]
                },
                "MongoDB Chat Memory Node": {
                  "ai_memory": [[{"node": "AI Agent Node", "type": "ai_memory", "index": 0}]]
                },
                "MongoDB Atlas Vector Store Node": {
                  "ai_tool": [[{"node": "AI Agent Node", "type": "ai_tool", "index": 0}]]
                }
            }
        }
        return workflow
