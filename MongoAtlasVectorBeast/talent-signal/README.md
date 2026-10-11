# ⚡ TalentSignal — Vector Search Swarm Topology Engine

> **Visual Graph Topology Compiler & Swarm Agent Network for MongoDB Atlas Vector Search**

---

## 🌟 System Overview

**TalentSignal** is a visual graph compiler and multi-agent swarm network designed for high-performance MongoDB Atlas Vector Search pipelines.

### Key Differentiators:
1. **Topology AST Compiler:** Canvas edge connections translate directly into executable MongoDB Aggregation Pipelines. Moving a `Filter` node before `VectorSearch` recompiles the query into an $O(\log N)$ native pre-filter `$match` stage.
2. **MongoDB AI & Voyage AI Integration:** Native support for MongoDB AI embeddings (`https://ai.mongodb.com/v1/embeddings` using `voyage-4-large`) and Voyage AI cross-encoder reranking (`voyage-rerank-2`).
3. **8-Agent Swarm Network:**
   - `@ts_vector_bot`: Vector Search Architect
   - `@ts_topology_bot`: Swarm Topology Orchestrator
   - `@ts_skill_matcher`: Skill Matrix Matching Specialist
   - `@ts_rerank_bot`: Candidate Rerank Sentinel
   - `@ts_telemetry_bot`: Time-Series Telemetry Analyst
   - `@ts_mesh_bot`: Global Mesh & Sharding Specialist
   - `@ts_lucene_bot`: Lucene NLP Search Specialist
   - `@ts_executive_bot`: Executive Summarizer Agent

---

## 🚀 Execution & Testing

### Run Python Unit Tests
```bash
python3 -m unittest discover -s tests
```

### Run TypeScript Example
```bash
npx tsx src/example.ts
```

### Run Standalone MVP Compiler
```bash
node demo.js
```
