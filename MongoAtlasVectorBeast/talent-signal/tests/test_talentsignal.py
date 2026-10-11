"""
Unit tests for TalentSignal Topology Compiler & Swarm Agent Network
"""

import json
import unittest
from app.personas import TALENTSIGNAL_SWARM_PERSONAS, get_persona_by_id
from app.node_agents import TALENTSIGNAL_NODE_AGENTS, get_node_agent_by_id
from app.compiler import compile_workflow_graph
from app.atlas_client import TalentSignalAtlasClient
from app.tools import (
    list_talentsignal_swarm_personas,
    list_talentsignal_canvas_node_agents,
    compile_talentsignal_topology,
    record_talentsignal_session,
    fetch_talentsignal_session
)

class TestTalentSignalSystem(unittest.TestCase):
    def setUp(self):
        self.client = TalentSignalAtlasClient()

    def test_swarm_personas_completeness(self):
        personas = list_talentsignal_swarm_personas()
        self.assertEqual(len(personas), 8)
        handles = [p["handle"] for p in personas]
        self.assertIn("@ts_vector_bot", handles)
        self.assertIn("@ts_topology_bot", handles)
        self.assertIn("@ts_rerank_bot", handles)

    def test_canvas_node_agents_completeness(self):
        nodes = list_talentsignal_canvas_node_agents()
        self.assertEqual(len(nodes), 6)
        node_ids = [n["node_id"] for n in nodes]
        self.assertIn("ts-mongodb-ai-embedding-node", node_ids)
        self.assertIn("ts-rerank-node", node_ids)
        self.assertIn("ts-filter-node", node_ids)

    def test_pre_filter_topology_compilation(self):
        graph = {
            "id": "ts_graph_demo",
            "name": "TalentSignal Pre-Filter Vector Pipeline",
            "nodes": [
                {"id": "n1", "type": "dataSource", "config": {"collection": "employees"}},
                {"id": "n2", "type": "filter", "config": {"field": "department", "op": "eq", "value": "Platform Engineering"}},
                {"id": "n3", "type": "mongoDbAiEmbedding", "config": {"index": "review_vector_index", "queryText": "Cloud architects", "limit": 20}},
                {"id": "n4", "type": "rerank", "config": {"provider": "voyage", "model": "voyage-rerank-2", "topK": 5}},
                {"id": "n5", "type": "llmAgent", "config": {"provider": "anthropic", "model": "claude-sonnet-5"}}
            ],
            "edges": [
                {"id": "e1", "source": "n1", "target": "n2"},
                {"id": "e2", "source": "n2", "target": "n3"},
                {"id": "e3", "source": "n3", "target": "n4"},
                {"id": "e4", "source": "n4", "target": "n5"}
            ]
        }
        res = compile_talentsignal_topology(graph)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["atlasEmbeddingMode"], "mongodb_ai_voyage")
        pipeline = res["pipeline"]
        self.assertIn("$match", pipeline[0])
        self.assertIn("$vectorSearch", pipeline[1])
        self.assertEqual(pipeline[1]["$vectorSearch"]["embeddingEndpoint"], "https://ai.mongodb.com/v1/embeddings")

    def test_session_chat_memory_persistence(self):
        rec = record_talentsignal_session("session_ts_999", "user", "Show me top vector matched candidates.")
        self.assertEqual(rec["status"], "persisted")
        
        hist = fetch_talentsignal_session("session_ts_999")
        self.assertEqual(hist["count"], 1)
        self.assertEqual(hist["history"][0]["message"], "Show me top vector matched candidates.")

if __name__ == "__main__":
    unittest.main()
