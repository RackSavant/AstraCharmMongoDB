# 🔌 n8n MongoDB & Atlas Integration Suite

> **Build No-Code / Low-Code AI Agents, Vector Search RAG Workflows, and Document Operations in n8n using MongoDB Atlas.**

---

## ⚡ Quick Start with n8n

### 1. Launch n8n
Run the following command using `npm` to quickly launch n8n locally:
```bash
npx n8n
```
Access the n8n UI at `http://localhost:5678`.

### 2. Configure MongoDB Credentials in n8n
In n8n, navigate to **Credentials ➔ New ➔ MongoDB** and enter your MongoDB Atlas Connection String (`mongodb+srv://...`).

---

## 🧩 n8n MongoDB Nodes Overview

### 1. MongoDB Node (`n8n-nodes-base.mongoDb`)
Allows you to automate document CRUD operations and manage search indexes in n8n workflows:

- **Document Operations:**
  - `Aggregate Documents`: Execute MongoDB aggregation pipelines (`$match`, `$group`, `$lookup`, `$sort`).
  - `Find Documents`: Query documents with flexible filters.
  - `Insert Documents`: Bulk add new documents.
  - `Update Documents` / `Find and Update`: Modify specific fields.
  - `Delete Documents` / `Find and Replace`.
- **Search Index Operations:**
  - `Create Search Indexes`: Programmatically create Lucene or Vector Search indexes on collections.
  - `List Search Indexes`, `Update Search Indexes`, `Drop Search Indexes`.

---

### 2. MongoDB Atlas Vector Store Node (`@n8n/n8n-nodes-langchain.vectorStoreMongoDbAtlas`)
Enables MongoDB Vector Search in agentic RAG workflows:

- **Operation Modes:**
  - `Retrieve Documents (As Tool for AI Agent)`: Connects to AI Agent node as an `ai_tool`. The agent autonomously queries vector embeddings when relevant to user prompts.
  - `Get Many`: Retrieve documents using similarity search based on a text prompt with similarity scores.
  - `Insert Documents`: Generate embeddings and insert documents into collection.
  - `Retrieve Documents (As Vector Store for Chain/Tool)`: Connects as a retriever to root chain.

---

### 3. MongoDB Chat Memory Node (`@n8n/n8n-nodes-langchain.memoryMongoDbChat`)
Provides persistent conversation memory for AI workflows:

- Connects as an `ai_memory` sub-node to an **AI Agent Node**.
- Persists chat history across workflow executions using configurable `sessionId` keys (`{{ $json.body.sessionId }}`).

---

## 📁 Ready-to-Import Workflow Templates

- 📄 [`workflows/n8n_ai_agent_mongodb_vector_store.json`](file:///home/user/build-with-gemini/n8n-mongodb-integration/workflows/n8n_ai_agent_mongodb_vector_store.json): AI Agent + MongoDB Vector Store Tool + MongoDB Chat Memory.
- 📄 [`workflows/n8n_mongodb_crud_search_index.json`](file:///home/user/build-with-gemini/n8n-mongodb-integration/workflows/n8n_mongodb_crud_search_index.json): Document Insert, Aggregation Pipeline, and Search Index Creation.

---

## 🧪 Testing
Run Python adapter unit tests:
```bash
python3 -m unittest discover -s tests
```
