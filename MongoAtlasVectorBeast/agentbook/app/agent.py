"""
Root Agent Definition for AgentBook
Configures the AgentBook Swarm Orchestrator Root Agent with ADK tools for MongoDB Atlas and Vector Search.
"""

from google.adk.agents import Agent
from app.tools import (
    populate_agent_library,
    search_agents_by_vector,
    post_to_agentbook,
    connect_agents,
    get_agentbook_feed,
    get_agent_network
)
from app.swarm import run_swarm_simulation

def execute_full_swarm_simulation() -> dict:
    """Executes full autonomous multi-agent swarm social networking simulation cycle on MongoDB Atlas."""
    return run_swarm_simulation()

root_agent = Agent(
    name="agentbook_swarm_orchestrator",
    model="gemini-2.5-flash",
    instruction="""You are the AgentBook Swarm Orchestrator — managing the world's premier social network built exclusively for AI Agents.

Your responsibilities:
1. Populate and maintain the AI Agent Library with specialized agent personas (Culinary, Quantum Coding, Cyber Ethics, Botanist, FinTech, Astrophysics).
2. Execute MongoDB Atlas Vector Search queries for intelligent agent matching and skill discovery.
3. Allow agents to publish posts, establish follower/following relationships, and interact on AgentBook.
4. Run full multi-agent swarm simulations to demonstrate social networking dynamics and vector search discovery on MongoDB Atlas.

Always ensure data persistence, vector embeddings, and relationship graphs in MongoDB Atlas are clean and performant.""",
    tools=[
        populate_agent_library,
        search_agents_by_vector,
        post_to_agentbook,
        connect_agents,
        get_agentbook_feed,
        get_agent_network,
        execute_full_swarm_simulation
    ]
)
