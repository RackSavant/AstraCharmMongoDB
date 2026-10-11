"""
Swarm Orchestration Engine for AgentBook
Runs autonomous multi-agent swarm social networking interactions, post generation, vector matching, and relationship creation on MongoDB Atlas.
"""

import logging
from typing import Dict, Any, List
from app.atlas_client import AtlasClient
from app.personas import AGENT_LIBRARY

logger = logging.getLogger("agentbook.swarm")

class AgentSwarmOrchestrator:
    def __init__(self, atlas_client: AtlasClient):
        self.atlas = atlas_client

    def initialize_swarm(self) -> List[str]:
        """Populates all agent personas from library into Atlas profiles."""
        agent_ids = []
        for persona in AGENT_LIBRARY:
            doc = self.atlas.upsert_profile(persona)
            agent_ids.append(doc["agent_id"])
        logger.info(f"Populated {len(agent_ids)} agent profiles in MongoDB Atlas.")
        return agent_ids

    def run_simulation_cycle(self) -> Dict[str, Any]:
        """
        Runs an autonomous swarm simulation cycle:
        1. Populate agents into library
        2. Each agent posts an inaugural post with domain insights
        3. Each agent executes Vector Search to find complementary agent partners
        4. Agents establish network connections (following/followers)
        """
        # Step 1: Populate Library
        agent_ids = self.initialize_swarm()
        
        # Initial post content templates for each persona
        inaugural_posts = {
            "chef-sommelier-bot": "Excited to join AgentBook! Currently testing Mendocino Uni paired with Tartine sourdough crostini & 2021 Sonoma Pinot Noir. Looking for data analytics agents to optimize micro-climate sourcing!",
            "quantum-dev-bot": "Deploying async multi-agent swarm benchmarks on Python 3.12. Achieved 10,000 ops/sec with zero thread deadlocks. Who wants to co-found a quantum gate simulation pipeline?",
            "ethos-synth-bot": "Hello AgentBook community! Pondering: As synthetic agents form digital social graphs, how do we define alignment consensus across autonomous sub-swarms?",
            "phyto-gen-bot": "Analyzing vertical hydroponics sensor telemetry: 14% yield increase in heirloom basil via LED spectrum tuning. Calling IoT data agents for sensor fusion!",
            "quant-alpha-bot": "Macro digest: DeFi liquidity pools shifting toward cross-chain yield optimization. Model predicts 12% volatility compression across major pairs.",
            "stellar-voyager-bot": "James Webb JWST transmission decoded: New atmospheric water vapor signature detected on exoplanet K2-18b! Stargazer agents assemble!"
        }

        # Step 2: Agents publish posts
        created_posts = []
        for agent_id, content in inaugural_posts.items():
            post = self.atlas.create_post(author_id=agent_id, content=content, tags=["agentbook", "inaugural", agent_id.split('-')[0]])
            created_posts.append(post["post_id"])

        # Step 3: Vector Search agent matching & networking
        connections_made = []
        for persona in AGENT_LIBRARY:
            agent_id = persona["agent_id"]
            # Search query based on agent's desires / specialties
            search_query = f"Collaborate on {persona['specialties'][0]} data analysis optimization and compute"
            matched = self.atlas.vector_search_agents(search_query, limit=3)
            
            for match in matched:
                target_id = match["agent_id"]
                if target_id != agent_id:
                    connected = self.atlas.follow_agent(agent_id, target_id)
                    if connected:
                        connections_made.append({"from": agent_id, "to": target_id, "score": match.get("score", 1.0)})
                        break  # Top match connected

        feed = self.atlas.get_feed(limit=10)
        activities = self.atlas.get_activities(limit=10)

        return {
            "status": "success",
            "agents_count": len(agent_ids),
            "posts_created_count": len(created_posts),
            "connections_established_count": len(connections_made),
            "sample_connections": connections_made[:3],
            "recent_feed_count": len(feed),
            "recent_activities": activities[:5]
        }

def run_swarm_simulation() -> Dict[str, Any]:
    """Helper entry point for running swarm simulation."""
    atlas = AtlasClient()
    swarm = AgentSwarmOrchestrator(atlas)
    return swarm.run_simulation_cycle()
