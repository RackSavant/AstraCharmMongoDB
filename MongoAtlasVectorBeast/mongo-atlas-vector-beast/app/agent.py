"""
Root Orchestrator Agent for MongoAtlasVectorBeast
"""

from google.adk.agents import Agent
from app.tools import (
    list_canvas_node_agents,
    compile_canvas_graph_pipeline,
    record_session_memory,
    fetch_session_memory
)

root_agent = Agent(
    name="mongo_atlas_vector_beast_orchestrator",
    model="gemini-2.5-flash",
    instruction="""You are the MongoAtlasVectorBeast Orchestrator Agent.

Your capabilities:
1. Provide access to 8 modular canvas node agents (VectorSearch, Filter, LLMAgent, Memory, TimeSeries, ChangeStream, GraphJoin, SearchIndex).
2. Compile visual workflow graphs into native MongoDB Atlas Aggregation Pipelines.
3. Manage MongoDB Chat Memory and session persistence.""",
    tools=[
        list_canvas_node_agents,
        compile_canvas_graph_pipeline,
        record_session_memory,
        fetch_session_memory
    ]
)
