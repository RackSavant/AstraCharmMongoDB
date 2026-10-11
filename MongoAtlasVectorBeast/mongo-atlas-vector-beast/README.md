# 🐉 MongoAtlasVectorBeast — Canvas Node Agents Suite

> **Modular AI Agents Designed to be Instantiated as Visual Nodes in n8n & Workflow Graph Compilers**

---

## 🧩 8 Modular Canvas Node Agents

1. **`VectorSearchNodeAgent`** (`vector-search-node`): Configures and compiles `$vectorSearch` KNN index stages.
2. **`FilterNodeAgent`** (`filter-node`): Generates dynamic `$match` pre/post query filters.
3. **`LLMAgentNodeAgent`** (`llm-agent-node`): Multi-provider LLM executor (`Gemini`, `OpenAI`, `Anthropic`).
4. **`MemoryNodeAgent`** (`chat-memory-node`): Manages MongoDB Chat Memory session persistence.
5. **`TimeSeriesNodeAgent`** (`time-series-node`): Handles time-series telemetry aggregations.
6. **`ChangeStreamNodeAgent`** (`change-stream-node`): Listens for real-time MongoDB CDC event streams.
7. **`GraphJoinNodeAgent`** (`graph-join-node`): Compiles relational `$lookup` joins across collections.
8. **`SearchIndexNodeAgent`** (`search-index-node`): Manages HNSW vector and Lucene search index schemas.

---

## 🧪 Testing
```bash
python3 -m unittest discover -s tests
```
