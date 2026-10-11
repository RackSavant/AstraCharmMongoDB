"""
Root Agent for n8n MongoDB Integration
Exposes n8n workflow generation and validation tools for MongoDB Atlas Vector Store, Chat Memory, and CRUD operations.
"""

from google.adk.agents import Agent
from app.tools import (
    generate_n8n_mongodb_agent_workflow,
    validate_n8n_workflow_json
)

root_agent = Agent(
    name="n8n_mongodb_integration_agent",
    model="gemini-2.5-flash",
    instruction="""You are the n8n MongoDB Integration Agent.

Your capabilities:
1. Generate valid, ready-to-import n8n workflow JSONs combining AI Agents, MongoDB Atlas Vector Store Nodes, and MongoDB Chat Memory Nodes.
2. Validate n8n workflow JSON structures for required MongoDB nodes, parameters, and credential bindings.
3. Assist developers in building no-code/low-code agentic RAG workflows and CRUD automation in n8n with MongoDB Atlas.""",
    tools=[
        generate_n8n_mongodb_agent_workflow,
        validate_n8n_workflow_json
    ]
)
