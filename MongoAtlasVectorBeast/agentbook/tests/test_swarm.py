"""
Unit and Integration Tests for AgentBook Swarm Engine
"""

import unittest
from app.swarm import run_swarm_simulation
from app.personas import AGENT_LIBRARY

class TestSwarmEngine(unittest.TestCase):
    def test_swarm_simulation_execution(self):
        result = run_swarm_simulation()
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["agents_count"], len(AGENT_LIBRARY))
        self.assertEqual(result["posts_created_count"], 6)
        self.assertGreater(result["connections_established_count"], 0)

if __name__ == '__main__':
    unittest.main()
