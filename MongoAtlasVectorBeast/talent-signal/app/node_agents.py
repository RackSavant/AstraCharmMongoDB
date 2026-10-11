"""
TalentSignal Node Agents Catalog — Modular Canvas Topology Node Agents
"""

from typing import Dict, Any, List

TALENTSIGNAL_NODE_AGENTS: List[Dict[str, Any]] = [
    {
        "node_type": "TalentSignalMongoDbAiEmbeddingNodeAgent",
        "node_id": "ts-mongodb-ai-embedding-node",
        "node_name": "TalentSignal MongoDB AI Voyage Embedding Node",
        "category": "Vector AI",
        "description": "Generates voyage-4-large embeddings via MongoDB AI endpoint (https://ai.mongodb.com/v1/embeddings).",
        "config_schema": {
            "index": "candidate_vector_index",
            "field": "resume_embedding",
            "queryText": "{{job_description}}",
            "limit": 20,
            "embeddingEndpoint": "https://ai.mongodb.com/v1/embeddings",
            "model": "voyage-4-large"
        },
        "inputs": ["queryText", "filterCondition"],
        "outputs": ["embedded_candidates"]
    },
    {
        "node_type": "TalentSignalRerankNodeAgent",
        "node_id": "ts-rerank-node",
        "node_name": "TalentSignal Voyage Rerank Node",
        "category": "Candidate Re-scoring",
        "description": "Executes voyage-rerank-2 cross-encoder scoring on candidate search results before LLM processing.",
        "config_schema": {
            "provider": "voyage",
            "model": "voyage-rerank-2",
            "topK": 5
        },
        "inputs": ["candidate_matches", "query"],
        "outputs": ["reranked_candidates"]
    },
    {
        "node_type": "TalentSignalFilterNodeAgent",
        "node_id": "ts-filter-node",
        "node_name": "TalentSignal Pre/Post Match Filter Node",
        "category": "Query Compilation",
        "description": "Compiles dynamic $match query stages. Positioning before VectorSearch optimizes query via pre-filtering.",
        "config_schema": {
            "field": "department",
            "op": "eq",
            "value": "Platform Engineering"
        },
        "inputs": ["documents"],
        "outputs": ["filtered_documents"]
    },
    {
        "node_type": "TalentSignalVectorSearchNodeAgent",
        "node_id": "ts-vector-search-node",
        "node_name": "TalentSignal Atlas Vector Search Node",
        "category": "Vector Search",
        "description": "Executes MongoDB Atlas $vectorSearch KNN similarity pipeline stages.",
        "config_schema": {
            "index": "talent_vector_index",
            "field": "embedding",
            "limit": 10,
            "numCandidates": 100
        },
        "inputs": ["queryVector", "filterCondition"],
        "outputs": ["matched_candidates"]
    },
    {
        "node_type": "TalentSignalLLMAgentNodeAgent",
        "node_id": "ts-llm-agent-node",
        "node_name": "TalentSignal Multi-Provider LLM Agent Node",
        "category": "LLM Inference",
        "description": "Executes candidate profile synthesis with Claude Sonnet 5, GPT-4o, or Gemini 2.5 Flash.",
        "config_schema": {
            "provider": "anthropic",
            "model": "claude-sonnet-5",
            "promptTemplate": "Synthesize why these reranked candidates match:\n{{documents}}",
            "outputField": "summary"
        },
        "inputs": ["documents", "prompt"],
        "outputs": ["executive_summary"]
    },
    {
        "node_type": "TalentSignalMemoryNodeAgent",
        "node_id": "ts-chat-memory-node",
        "node_name": "TalentSignal Chat Memory Node",
        "category": "Session Memory",
        "description": "Persists talent search conversation turns in MongoDB chat_memory_sessions collection.",
        "config_schema": {
            "collectionName": "chat_memory_sessions",
            "sessionKey": "sessionId"
        },
        "inputs": ["sessionId", "user_message"],
        "outputs": ["conversation_history"]
    }
]

def get_node_agent_by_id(node_id: str) -> Dict[str, Any]:
    for agent in TALENTSIGNAL_NODE_AGENTS:
        if agent["node_id"] == node_id:
            return agent
    return TALENTSIGNAL_NODE_AGENTS[0]
