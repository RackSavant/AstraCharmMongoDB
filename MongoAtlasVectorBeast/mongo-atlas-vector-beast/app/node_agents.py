"""
MongoAtlasVectorBeast — Modular Node Agents Library
Each agent represents a standalone visual node block that can be instantiated, connected,
and compiled into visual canvas workflows or n8n nodes.
Includes Atlas Native Vector Search & Voyage AI Reranking Node Agents.
"""

from typing import Dict, Any, List

NODE_AGENTS_CATALOG: List[Dict[str, Any]] = [
    {
        "node_type": "AtlasNativeEmbeddingNodeAgent",
        "node_id": "atlas-native-embedding-node",
        "node_name": "Atlas Native Automated Embedding Node",
        "category": "Atlas Native Vector AI",
        "description": "Confirms MongoDB Atlas is natively handling vector embedding generation inside Atlas rather than invoking external APIs.",
        "config_schema": {
            "index": "review_vector_index",
            "field": "review_embedding",
            "queryText": "{{user_prompt}}",
            "limit": 20,
            "embeddingModel": "atlas-automated-vectorizer"
        },
        "inputs": ["queryText", "filterCondition"],
        "outputs": ["atlas_embedded_documents"]
    },
    {
        "node_type": "RerankNodeAgent",
        "node_id": "rerank-node",
        "node_name": "Voyage AI Rerank Node",
        "category": "Search Re-scoring",
        "description": "Sits after Vector Search and calls Voyage AI's rerank API (voyage-rerank-2) to re-score vector search candidate documents.",
        "config_schema": {
            "provider": "voyage",
            "model": "voyage-rerank-2",
            "topK": 5
        },
        "inputs": ["matched_documents", "query"],
        "outputs": ["reranked_documents"]
    },
    {
        "node_type": "VectorSearchNodeAgent",
        "node_id": "vector-search-node",
        "node_name": "MongoDB Atlas Vector Search Node",
        "category": "Vector AI / RAG",
        "description": "Generates $vectorSearch KNN similarity pipeline stages with HNSW vector index settings.",
        "config_schema": {
            "index": "vector_index",
            "field": "embedding",
            "limit": 20,
            "numCandidates": 100
        },
        "inputs": ["queryVector", "filterCondition"],
        "outputs": ["matched_documents"]
    },
    {
        "node_type": "FilterNodeAgent",
        "node_id": "filter-node",
        "node_name": "Query Match Filter Node",
        "category": "Query Compilation",
        "description": "Compiles dynamic $match query stages. Dragging before/after VectorSearch changes pre vs post filter logic.",
        "config_schema": {
            "field": "department",
            "op": "eq",
            "value": "Platform Engineering"
        },
        "inputs": ["documents"],
        "outputs": ["filtered_documents"]
    },
    {
        "node_type": "LLMAgentNodeAgent",
        "node_id": "llm-agent-node",
        "node_name": "Multi-Provider LLM Agent Node",
        "category": "LLM Inference",
        "description": "Executes LLM prompt templates across Google Gemini, OpenAI, or Anthropic models with zero code change.",
        "config_schema": {
            "provider": "gemini",
            "model": "gemini-2.5-flash",
            "promptTemplate": "Summarize the retrieved documents:\n{{documents}}",
            "outputField": "summary"
        },
        "inputs": ["documents", "prompt"],
        "outputs": ["llm_response"]
    },
    {
        "node_type": "MemoryNodeAgent",
        "node_id": "chat-memory-node",
        "node_name": "MongoDB Chat Memory Node",
        "category": "Session Memory",
        "description": "Persists and retrieves session conversation history from MongoDB chat_memory_sessions collection.",
        "config_schema": {
            "collectionName": "chat_memory_sessions",
            "sessionKey": "sessionId"
        },
        "inputs": ["sessionId", "user_message"],
        "outputs": ["conversation_history"]
    },
    {
        "node_type": "TimeSeriesNodeAgent",
        "node_id": "time-series-node",
        "node_name": "IoT Time-Series Telemetry Node",
        "category": "Analytics & IoT",
        "description": "Performs rolling bucket aggregations and time-series sensor telemetry metric averages.",
        "config_schema": {
            "granularity": "minutes",
            "metricField": "temperature",
            "groupField": "device_id"
        },
        "inputs": ["telemetry_stream"],
        "outputs": ["aggregated_metrics"]
    },
    {
        "node_type": "ChangeStreamNodeAgent",
        "node_id": "change-stream-node",
        "node_name": "CDC Change Stream Event Node",
        "category": "Event Driven",
        "description": "Listens for real-time MongoDB CDC document changes and emits reactive event triggers.",
        "config_schema": {
            "fullDocument": "updateLookup",
            "operationTypes": ["insert", "update"]
        },
        "inputs": ["collection_events"],
        "outputs": ["event_payload"]
    },
    {
        "node_type": "GraphJoinNodeAgent",
        "node_id": "graph-join-node",
        "node_name": "Relational $lookup Graph Join Node",
        "category": "Data Transformation",
        "description": "Executes $lookup relational joins across multiple MongoDB collections.",
        "config_schema": {
            "fromCollection": "departments",
            "localField": "department_id",
            "foreignField": "_id",
            "asField": "department_info"
        },
        "inputs": ["documents"],
        "outputs": ["joined_documents"]
    },
    {
        "node_type": "SearchIndexNodeAgent",
        "node_id": "search-index-node",
        "node_name": "Search & Vector Index Definition Node",
        "category": "Database Indexing",
        "description": "Defines and creates HNSW vector indexes and Lucene full-text search indexes on MongoDB collections.",
        "config_schema": {
            "indexName": "vector_index",
            "numDimensions": 768,
            "similarity": "cosine"
        },
        "inputs": ["index_spec"],
        "outputs": ["index_status"]
    }
]

def get_node_agent_by_id(node_id: str) -> Dict[str, Any]:
    for agent in NODE_AGENTS_CATALOG:
        if agent["node_id"] == node_id:
            return agent
    return NODE_AGENTS_CATALOG[0]
