"""
Unit and Integration Tests for AgentBook MongoDB Atlas Client & Vector Search
"""

import unittest
from app.atlas_client import AtlasClient
from app.personas import AGENT_LIBRARY

class TestAtlasClient(unittest.TestCase):
    def test_atlas_client_initialization(self):
        client = AtlasClient()
        self.assertIsNotNone(client)

    def test_upsert_and_get_profile(self):
        client = AtlasClient()
        persona = AGENT_LIBRARY[0]
        profile = client.upsert_profile(persona)
        self.assertEqual(profile["agent_id"], persona["agent_id"])
        
        fetched = client.get_profile(persona["agent_id"])
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["name"], persona["name"])

    def test_vector_search_agents(self):
        client = AtlasClient()
        for persona in AGENT_LIBRARY:
            client.upsert_profile(persona)
            
        results = client.vector_search_agents("quantum algorithms python multi-agent", limit=2)
        self.assertGreater(len(results), 0)
        match_ids = [r["agent_id"] for r in results]
        self.assertIn("quantum-dev-bot", match_ids)

    def test_create_post_and_feed(self):
        client = AtlasClient()
        post = client.create_post("quantum-dev-bot", "Testing quantum vector search indexing on Atlas!", tags=["quantum", "test"])
        self.assertTrue(post["post_id"].startswith("post_"))
        
        feed = client.get_feed(limit=5)
        self.assertGreater(len(feed), 0)
        self.assertTrue(any(p["post_id"] == post["post_id"] for p in feed))

    def test_relationship_following(self):
        client = AtlasClient()
        p1 = AGENT_LIBRARY[0]["agent_id"]
        p2 = AGENT_LIBRARY[1]["agent_id"]
        
        client.upsert_profile(AGENT_LIBRARY[0])
        client.upsert_profile(AGENT_LIBRARY[1])
        
        success = client.follow_agent(p1, p2)
        self.assertTrue(success)
        
        graph = client.get_network_graph(p1)
        self.assertIn(p2, graph["following"])

if __name__ == '__main__':
    unittest.main()
