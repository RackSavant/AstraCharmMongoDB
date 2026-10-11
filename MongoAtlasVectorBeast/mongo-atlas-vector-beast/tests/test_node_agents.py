"""
Unit tests for MongoAtlasVectorBeast Node Agents and Execution Engine
"""

import json
import unittest
from app.node_agents import NODE_AGENTS_CATALOG, get_node_agent_by_id
from app.atlas_engine import VectorBeastEngine
from app.tools import (
    list_canvas_node_agents,
    compile_canvas_graph_pipeline,
    record_session_memory,
    fetch_session_memory
)

class TestVectorBeastNodeAgents(unittest.TestCase):
    def setUp(self):
        self.engine = VectorBeastEngine()

    def test_node_catalog_completeness(self):
        catalog = list_canvas_node_agents()
        self.assertEqual(len(catalog), 10)
        node_types = [n["node_type"] for n in catalog]
        self.assertIn("AtlasNativeEmbeddingNodeAgent", node_types)
        self.assertIn("RerankNodeAgent", node_types)
        self.assertIn("VectorSearchNodeAgent", node_types)
        self.assertIn("FilterNodeAgent", node_types)
        self.assertIn("LLMAgentNodeAgent", node_types)

    def test_pipeline_compilation_from_workflow_json(self):
        with open("workflows/vector_beast_pipeline.json") as f:
            wf = json.load(f)
        res = compile_canvas_graph_pipeline(wf)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["nodes_count"], 4)
        pipeline = res["compiled_pipeline"]
        self.assertIn("$match", pipeline[0])
        self.assertIn("$vectorSearch", pipeline[1])
        self.assertIn("$lookup", pipeline[2])

    def test_session_memory_persistence(self):
        rec = record_session_memory("test_session_101", "user", "Hello Vector Beast!")
        self.assertEqual(rec["status"], "persisted")
        
        hist = fetch_session_memory("test_session_101")
        self.assertEqual(hist["count"], 1)
        self.assertEqual(hist["history"][0]["message"], "Hello Vector Beast!")

if __name__ == "__main__":
    unittest.main()
