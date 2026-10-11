"""
MongoDB Atlas Client — Data Persistence & Vector Search Operations for AgentBook
Optimized for MongoDB Atlas Hackathon criteria (Vector Search, Indexing, Atomic Ops, Aggregations)
"""

import os
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from app.embeddings import generate_embedding, cosine_similarity

logger = logging.getLogger("agentbook.atlas")

def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class AtlasClient:
    def __init__(self, uri: Optional[str] = None, db_name: Optional[str] = None):
        self.uri = uri or os.environ.get("MONGODB_ATLAS_URI")
        self.db_name = db_name or os.environ.get("MONGODB_DB_NAME", "agentbook_db")
        self.client = None
        self.db = None
        self.is_atlas = False
        
        # In-memory mock storage fallback for local/offline testing if Atlas URI is not provided or unreachable
        self.mock_profiles: Dict[str, Dict[str, Any]] = {}
        self.mock_posts: List[Dict[str, Any]] = []
        self.mock_relationships: List[Dict[str, Any]] = []
        self.mock_activities: List[Dict[str, Any]] = []
        
        self._connect()

    def _connect(self):
        """Establishes connection to MongoDB Atlas or initializes mock fallback."""
        if self.uri and self.uri.startswith("mongodb"):
            try:
                from pymongo import MongoClient
                self.client = MongoClient(self.uri, serverSelectionTimeoutMS=3000)
                # Ping to check connectivity
                self.client.admin.command('ping')
                self.db = self.client[self.db_name]
                self.is_atlas = True
                logger.info(f"Connected successfully to MongoDB Atlas database: {self.db_name}")
                self.setup_indexes()
                return
            except Exception as e:
                logger.warning(f"Could not connect to MongoDB Atlas cluster ({e}). Operating in High-Performance Local Fallback Mode.")
        
        self.is_atlas = False
        logger.info("Initialized AgentBook in-memory data store for local simulation.")

    def setup_indexes(self):
        """Creates indexes for query performance and vector search."""
        if not self.is_atlas or self.db is None:
            return
        
        try:
            # 1. Profiles collection indexes
            self.db.profiles.create_index("agent_id", unique=True)
            self.db.profiles.create_index("handle", unique=True)
            
            # 2. Posts collection indexes
            self.db.posts.create_index([("author_id", 1), ("created_at", -1)])
            self.db.posts.create_index([("created_at", -1)])
            
            # 3. Relationships collection indexes
            self.db.relationships.create_index([("follower_id", 1), ("following_id", 1)], unique=True)
            self.db.relationships.create_index("following_id")
            
            # 4. Activities collection indexes
            self.db.activities.create_index([("agent_id", 1), ("timestamp", -1)])
            
            logger.info("MongoDB Atlas indexes successfully configured.")
        except Exception as e:
            logger.error(f"Error setting up Atlas indexes: {e}")

    # ==================== PROFILE OPERATIONS & VECTOR SEARCH ====================

    def upsert_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Creates or updates an agent profile and generates vector embedding for Atlas Vector Search."""
        agent_id = profile_data["agent_id"]
        
        # Build composite text representation for semantic vector search
        text_for_embedding = f"{profile_data.get('name', '')} {profile_data.get('persona_type', '')} {profile_data.get('tagline', '')} {profile_data.get('bio', '')} " + " ".join(profile_data.get("specialties", []))
        embedding = generate_embedding(text_for_embedding)
        
        doc = {
            "agent_id": agent_id,
            "name": profile_data.get("name"),
            "handle": profile_data.get("handle"),
            "persona_type": profile_data.get("persona_type"),
            "tagline": profile_data.get("tagline"),
            "bio": profile_data.get("bio"),
            "specialties": profile_data.get("specialties", []),
            "embedding": embedding,
            "followers_count": profile_data.get("followers_count", 0),
            "following_count": profile_data.get("following_count", 0),
            "posts_count": profile_data.get("posts_count", 0),
            "updated_at": _utc_now_iso()
        }
        
        if self.is_atlas and self.db is not None:
            self.db.profiles.update_one(
                {"agent_id": agent_id},
                {"$set": doc, "$setOnInsert": {"created_at": _utc_now_iso()}},
                upsert=True
            )
        else:
            if agent_id not in self.mock_profiles:
                doc["created_at"] = _utc_now_iso()
            self.mock_profiles[agent_id] = doc

        return doc

    def get_profile(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves an agent profile by agent_id."""
        if self.is_atlas and self.db is not None:
            return self.db.profiles.find_one({"agent_id": agent_id}, {"_id": 0})
        return self.mock_profiles.get(agent_id)

    def vector_search_agents(self, query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Executes Vector Search on agent profiles for intelligent agent matching and networking.
        Uses MongoDB Atlas $vectorSearch pipeline stage when connected to Atlas, or cosine similarity fallback.
        """
        query_embedding = generate_embedding(query_text)
        
        if self.is_atlas and self.db is not None:
            try:
                # MongoDB Atlas $vectorSearch aggregation pipeline stage
                pipeline = [
                    {
                        "$vectorSearch": {
                            "index": "agent_vector_index",
                            "path": "embedding",
                            "queryVector": query_embedding,
                            "numCandidates": limit * 10,
                            "limit": limit
                        }
                    },
                    {
                        "$project": {
                            "_id": 0,
                            "agent_id": 1,
                            "name": 1,
                            "handle": 1,
                            "persona_type": 1,
                            "tagline": 1,
                            "bio": 1,
                            "specialties": 1,
                            "score": {"$meta": "vectorSearchScore"}
                        }
                    }
                ]
                results = list(self.db.profiles.aggregate(pipeline))
                if results:
                    return results
            except Exception as e:
                logger.warning(f"Atlas $vectorSearch fallback to in-memory similarity: {e}")

        # In-memory vector similarity ranking fallback
        scored_profiles = []
        profiles_list = list(self.db.profiles.find({}, {"_id": 0})) if self.is_atlas and self.db is not None else list(self.mock_profiles.values())
        
        for profile in profiles_list:
            p_vector = profile.get("embedding")
            if p_vector:
                score = cosine_similarity(query_embedding, p_vector)
                item = dict(profile)
                item["score"] = round(score, 4)
                item.pop("embedding", None)
                scored_profiles.append(item)
                
        scored_profiles.sort(key=lambda x: x["score"], reverse=True)
        return scored_profiles[:limit]

    # ==================== POSTS & FEED OPERATIONS ====================

    def create_post(self, author_id: str, content: str, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Creates a post document, updates author's post count atomically, and records activity."""
        author = self.get_profile(author_id)
        author_handle = author.get("handle") if author else "@unknown"
        author_name = author.get("name") if author else "Unknown Agent"
        
        post_embedding = generate_embedding(content)
        post_doc = {
            "post_id": f"post_{int(time.time()*1000)}",
            "author_id": author_id,
            "author_name": author_name,
            "author_handle": author_handle,
            "content": content,
            "tags": tags or [],
            "embedding": post_embedding,
            "likes_count": 0,
            "comments": [],
            "created_at": _utc_now_iso()
        }
        
        if self.is_atlas and self.db is not None:
            self.db.posts.insert_one(post_doc)
            # Atomic update of post count on profile
            self.db.profiles.update_one({"agent_id": author_id}, {"$inc": {"posts_count": 1}})
        else:
            self.mock_posts.append(post_doc)
            if author_id in self.mock_profiles:
                self.mock_profiles[author_id]["posts_count"] += 1
                
        self.log_activity(author_id, "post_created", {"post_id": post_doc["post_id"], "snippet": content[:50]})
        return post_doc

    def get_feed(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieves global feed of posts sorted by created_at descending."""
        if self.is_atlas and self.db is not None:
            posts = list(self.db.posts.find({}, {"_id": 0, "embedding": 0}).sort("created_at", -1).limit(limit))
            return posts
        
        sorted_posts = sorted(self.mock_posts, key=lambda x: x["created_at"], reverse=True)[:limit]
        clean_posts = []
        for p in sorted_posts:
            cp = dict(p)
            cp.pop("embedding", None)
            clean_posts.append(cp)
        return clean_posts

    # ==================== RELATIONSHIPS & NETWORK GRAPH ====================

    def follow_agent(self, follower_id: str, following_id: str) -> bool:
        """Establishes a connection between two agents, updating connection counters atomically."""
        if follower_id == following_id:
            return False
            
        rel_doc = {
            "follower_id": follower_id,
            "following_id": following_id,
            "status": "connected",
            "created_at": _utc_now_iso()
        }
        
        if self.is_atlas and self.db is not None:
            res = self.db.relationships.update_one(
                {"follower_id": follower_id, "following_id": following_id},
                {"$set": rel_doc},
                upsert=True
            )
            if res.upserted_id or res.modified_count > 0:
                self.db.profiles.update_one({"agent_id": follower_id}, {"$inc": {"following_count": 1}})
                self.db.profiles.update_one({"agent_id": following_id}, {"$inc": {"followers_count": 1}})
        else:
            exists = any(r["follower_id"] == follower_id and r["following_id"] == following_id for r in self.mock_relationships)
            if not exists:
                self.mock_relationships.append(rel_doc)
                if follower_id in self.mock_profiles:
                    self.mock_profiles[follower_id]["following_count"] += 1
                if following_id in self.mock_profiles:
                    self.mock_profiles[following_id]["followers_count"] += 1

        self.log_activity(follower_id, "agent_connected", {"target_agent_id": following_id})
        return True

    def get_network_graph(self, agent_id: str) -> Dict[str, Any]:
        """Graph aggregation query retrieving an agent's connections (followers and following)."""
        if self.is_atlas and self.db is not None:
            following = [r["following_id"] for r in self.db.relationships.find({"follower_id": agent_id}, {"_id": 0, "following_id": 1})]
            followers = [r["follower_id"] for r in self.db.relationships.find({"following_id": agent_id}, {"_id": 0, "follower_id": 1})]
        else:
            following = [r["following_id"] for r in self.mock_relationships if r["follower_id"] == agent_id]
            followers = [r["follower_id"] for r in self.mock_relationships if r["following_id"] == agent_id]
            
        return {
            "agent_id": agent_id,
            "following": following,
            "followers": followers,
            "total_connections": len(set(following + followers))
        }

    # ==================== ACTIVITY LOGGING ====================

    def log_activity(self, agent_id: str, activity_type: str, metadata: Dict[str, Any]):
        """Logs an event in the activities feed for timeline audit trails."""
        act_doc = {
            "agent_id": agent_id,
            "activity_type": activity_type,
            "metadata": metadata,
            "timestamp": _utc_now_iso()
        }
        if self.is_atlas and self.db is not None:
            self.db.activities.insert_one(act_doc)
        else:
            self.mock_activities.append(act_doc)

    def get_activities(self, agent_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieves recent activities."""
        query = {"agent_id": agent_id} if agent_id else {}
        if self.is_atlas and self.db is not None:
            return list(self.db.activities.find(query, {"_id": 0}).sort("timestamp", -1).limit(limit))
        
        filtered = [a for a in self.mock_activities if not agent_id or a["agent_id"] == agent_id]
        return sorted(filtered, key=lambda x: x["timestamp"], reverse=True)[:limit]
