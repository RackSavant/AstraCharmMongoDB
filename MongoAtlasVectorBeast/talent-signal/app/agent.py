"""
TalentSignal Root Swarm Orchestrator Agent
"""

from google.adk.agents import Agent
from app.tools import (
    list_talentsignal_swarm_personas,
    list_talentsignal_canvas_node_agents,
    compile_talentsignal_topology,
    record_talentsignal_session,
    fetch_talentsignal_session
)

root_agent = Agent(
    name="talentsignal_swarm_orchestrator",
    model="gemini-2.5-flash",
    instruction="""You are the TalentSignal Swarm Orchestrator Agent.

Your capabilities:
1. Manage 8 specialized TalentSignal Agent Swarm personas for vector candidate discovery.
2. Provide access to modular canvas node agents for visual topology design.
3. Compile visual canvas topology graphs into native MongoDB Atlas Aggregation Pipelines (with MongoDB AI Voyage-4-Large, Voyage Rerank, and Pre-Filter $match optimization).
4. Persist and retrieve conversation turns in TalentSignal MongoDB Chat Memory.""",
    tools=[
        list_talentsignal_swarm_personas,
        list_talentsignal_canvas_node_agents,
        compile_talentsignal_topology,
        record_talentsignal_session,
        fetch_talentsignal_session
    ]
)
