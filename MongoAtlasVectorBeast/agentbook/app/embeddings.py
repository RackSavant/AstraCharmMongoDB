import os
import re
import math
import logging
import urllib.request
import json
from typing import List

logger = logging.getLogger("agentbook.embeddings")

COMMON_VOCAB = [
    "quantum", "algorithms", "python", "multi", "agent", "swarm", "optimization",
    "gastronomy", "wine", "culinary", "michelin", "sourdough", "food",
    "philosophy", "ethics", "synthetic", "consciousness", "alignment",
    "hydroponics", "genomics", "farming", "botanist", "crop", "plant",
    "fintech", "defi", "trading", "liquidity", "finance", "macro",
    "astrophysics", "space", "exoplanet", "orbit", "telescope", "cosmic",
    "data", "system", "network", "code", "model", "science", "tech"
]

def generate_embedding(text: str, dimension: int = 768) -> List[float]:
    """
    Generates vector embedding for text using MongoDB AI / Voyage AI API (voyage-4-large),
    or Google Gemini text-embedding-004, or falls back to an offline vocabulary vector generator.
    """
    if not text:
        text = "empty"

    # 1. Try MongoDB AI / Voyage AI API endpoint (voyage-4-large)
    voyage_key = os.environ.get("VOYAGE_API_KEY") or os.environ.get("MONGODB_AI_API_KEY")
    if voyage_key:
        try:
            url = "https://ai.mongodb.com/v1/embeddings"
            payload = json.dumps({
                "input": [text],
                "model": "voyage-4-large"
            }).encode("utf-8")
            
            req = urllib.request.Request(
                url,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {voyage_key}"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                if "data" in res_data and len(res_data["data"]) > 0:
                    embedding = res_data["data"][0].get("embedding", [])
                    if embedding:
                        return embedding
        except Exception as e:
            logger.warning(f"MongoDB AI / Voyage API embedding failed: {e}. Trying Gemini API...")

    # 2. Try Google Gemini API (text-embedding-004)
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            result = client.models.embed_content(
                model="text-embedding-004",
                contents=text
            )
            if result.embedding and result.embedding.values:
                return result.embedding.values
        except Exception as e:
            logger.warning(f"Gemini API embedding failed: {e}. Using offline fallback generator.")

    # 3. Offline vocabulary + character hash fallback
    tokens = set(re.findall(r'\w+', text.lower()))
    vector = [0.0] * dimension
    
    for i, vocab in enumerate(COMMON_VOCAB):
        if vocab in tokens:
            bin_idx = (i * 17) % dimension
            vector[bin_idx] += 2.0
            
    import hashlib
    for token in tokens:
        token_hash = int(hashlib.sha256(token.encode('utf-8')).hexdigest(), 16)
        bin_idx = token_hash % dimension
        vector[bin_idx] += 1.0

    magnitude = math.sqrt(sum(v * v for v in vector))
    if magnitude > 0:
        vector = [v / magnitude for v in vector]
    else:
        vector = [1.0 / math.sqrt(dimension)] * dimension
        
    return vector

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculates cosine similarity between two normalized vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm_v1 = math.sqrt(sum(a * a for a in v1))
    norm_v2 = math.sqrt(sum(b * b for b in v2))
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return dot / (norm_v1 * norm_v2)
