"""
Unit tests for Talent Signal Workflow Compiler
"""

import unittest
from app.compiler import compile_workflow_graph, validate_workflow_graph

BASE_WORKFLOW_GRAPH = {
    "id": "wf_demo",
    "name": "Talent Signal — Demo Pipeline",
    "nodes": [
        {"id": "n1", "type": "dataSource", "config": {"collection": "employees"}},
        {"id": "n2", "type": "vectorSearch", "config": {"index": "review_vector_index", "field": "review_embedding", "limit": 20}},
        {"id": "n3", "type": "filter", "config": {"field": "department", "op": "eq", "value": "Platform Engineering"}},
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

class TestWorkflowCompiler(unittest.TestCase):
    def test_validation_base_workflow(self):
        errors = validate_workflow_graph(BASE_WORKFLOW_GRAPH)
        self.assertEqual(len(errors), 0)

    def test_base_workflow_compilation(self):
        compiled = compile_workflow_graph(BASE_WORKFLOW_GRAPH)
        self.assertEqual(compiled["status"], "success")
        self.assertEqual(len(compiled["pipeline"]), 2)
        self.assertIn("$vectorSearch", compiled["pipeline"][0])
        self.assertIn("$match", compiled["pipeline"][1])
        self.assertEqual(len(compiled["llmStages"]), 1)
        self.assertEqual(compiled["llmStages"][0]["provider"], "anthropic")

    def test_rewire_filter_before_vector_search(self):
        rewired_graph = {
            **BASE_WORKFLOW_GRAPH,
            "edges": [
                {"id": "e1", "source": "n1", "target": "n3"},
                {"id": "e2", "source": "n3", "target": "n2"},
                {"id": "e3", "source": "n2", "target": "n4"},
                {"id": "e4", "source": "n4", "target": "n5"}
            ]
        }
        plan = compile_workflow_graph(rewired_graph)
        self.assertEqual(plan["status"], "success")
        self.assertIn("$match", plan["pipeline"][0])
        self.assertIn("$vectorSearch", plan["pipeline"][1])

if __name__ == "__main__":
    unittest.main()
