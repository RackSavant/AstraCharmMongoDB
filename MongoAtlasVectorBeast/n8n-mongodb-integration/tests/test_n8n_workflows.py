"""
Unit tests for n8n MongoDB Integration workflows and adapter
"""

import json
import unittest
from app.n8n_adapter import N8nMongoDBAdapter
from app.tools import (
    generate_n8n_mongodb_agent_workflow,
    validate_n8n_workflow_json
)

class TestN8nMongoDBWorkflows(unittest.TestCase):
    def setUp(self):
        self.adapter = N8nMongoDBAdapter()

    def test_workflow_generation(self):
        res = generate_n8n_mongodb_agent_workflow(
            agent_name="Gourmet Concierge",
            system_prompt="You are a Michelin culinary concierge."
        )
        self.assertTrue(res["valid"])
        self.assertEqual(len(res["validation_errors"]), 0)
        wf = res["workflow"]
        self.assertEqual(wf["name"], "n8n AI Agent — Gourmet Concierge")
        self.assertEqual(len(wf["nodes"]), 5)

    def test_vector_store_workflow_json_template(self):
        with open("workflows/n8n_ai_agent_mongodb_vector_store.json") as f:
            data = json.load(f)
        errors = self.adapter.validate_n8n_workflow(data)
        self.assertEqual(len(errors), 0)

    def test_crud_search_index_workflow_json_template(self):
        with open("workflows/n8n_mongodb_crud_search_index.json") as f:
            data = json.load(f)
        errors = self.adapter.validate_n8n_workflow(data)
        self.assertEqual(len(errors), 0)

if __name__ == "__main__":
    unittest.main()
