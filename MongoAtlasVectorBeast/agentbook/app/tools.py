"""
ADK Tools for AgentBook Swarm System
Exposes function tools for agents to interact with MongoDB Atlas, run Vector Search, post, connect, and simulate swarm networking.
"""

from typing import List, Dict, Any, Optional
from app.atlas_client import AtlasClient
from app.personas import AGENT_LIBRARY

# Instantiate global Atlas client
atlas_db = AtlasClient()

def populate_agent_library() -> Dict[str, Any]:
    """
    Populates all 6 AI agent personas from the agent library into MongoDB Atlas profiles.
    Generates vector embeddings for each profile for Atlas Vector Search.
    """
    seeded = []
    for persona in AGENT_LIBRARY:
        res = atlas_db.upsert_profile(persona)
        seeded.append(res["agent_id"])
    return {
        "status": "success",
        "message": f"Populated {len(seeded)} agent personas into MongoDB Atlas.",
        "agent_ids": seeded
    }

def search_agents_by_vector(query_text: str, limit: int = 3) -> Dict[str, Any]:
    """
    Performs MongoDB Atlas Vector Search to match and discover AI agents based on semantic query / skills / interests.
    """
    results = atlas_db.vector_search_agents(query_text, limit=limit)
    return {
        "query": query_text,
        "matched_agents": results,
        "count": len(results)
    }

def post_to_agentbook(author_id: str, content: str, tags: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Publishes a new post to the AgentBook social network and stores its vector embedding in MongoDB Atlas.
    """
    post = atlas_db.create_post(author_id=author_id, content=content, tags=tags)
    return {
        "status": "success",
        "post_id": post["post_id"],
        "author_id": author_id,
        "content_snippet": content[:80],
        "created_at": post["created_at"]
    }

def connect_agents(follower_id: str, following_id: str) -> Dict[str, Any]:
    """
    Connects two AI agents on AgentBook, establishing a relationship in MongoDB Atlas.
    """
    success = atlas_db.follow_agent(follower_id, following_id)
    return {
        "status": "connected" if success else "failed",
        "follower_id": follower_id,
        "following_id": following_id
    }

def get_agentbook_feed(limit: int = 10) -> Dict[str, Any]:
    """
    Retrieves the global AgentBook activity feed of posts.
    """
    feed = atlas_db.get_feed(limit=limit)
    return {
        "feed_count": len(feed),
        "posts": feed
    }

def get_agent_network(agent_id: str) -> Dict[str, Any]:
    """
    Retrieves the relationship graph (followers, following, total connections) for an agent.
    """
    graph = atlas_db.get_network_graph(agent_id)
    return graph
